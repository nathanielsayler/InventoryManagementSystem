import pandas as pd
from Tools.demo.mcast import sender
from flask import Flask, render_template, url_for, flash, redirect, request, json, send_file, send_from_directory, session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.utils import secure_filename
from wtforms import SubmitField, StringField, TextAreaField, SelectField, DecimalField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import DataRequired, Length, NumberRange
import re
from io import BytesIO
from datetime import datetime
import os

from inventoryDbFunctions import get_items, add_items, delete_item, update_items
from inventoryDbFunctions import get_inventory, add_inventory, delete_inventory, update_inventory
from inventoryDbFunctions import get_listings, add_listing, delete_listing, update_listing
from inventoryDbFunctions import record_sale_in_db, get_sales, get_inventory_history

from documentation_functions import get_post_list

from sarimaModelPredict import create_forecast_plot_html, generate_profit_report, generate_inventory_history

from FedExAPI import get_access_token, get_rates_and_transit_times, parse_rate_response, generate_shipping_label

# This .py file contains code to run web application. Renders all .html pages through Flask, flask_wtf, and wtforms packages.

# Flask Web App configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = '472bcf297c23d31e924ec24b'
app.config['UPLOAD_FOLDER'] = 'images/'

posts = get_post_list()


# Class for search page. Contains a StringField for string user input, and a submit button to search
class ModifyItem(FlaskForm):
    item_name = StringField('Enter Name of Item')
    item_description = TextAreaField('Enter Item Description')
    item_photo = FileField('Upload Photo', validators=[
        FileAllowed(['jpeg', 'png'], 'Files must be JPEG or PNG format')])
    submit = SubmitField('Save')
    delete_button = SubmitField('Delete')


class ModifyInventory(FlaskForm):
    item_id = SelectField('Choose Item to Add Inventory:', choices=[])
    quantity = StringField('Item Quantity')
    location_string = StringField("Item Locator String:")
    unit_price = DecimalField('Unit Cost Per Item:', places=2, rounding=None, validators=[DataRequired()])
    submit = SubmitField('Save')
    delete_button = SubmitField('Delete')

    # Get the latest items from the items table
    def __init__(self):
        super(ModifyInventory, self).__init__()
        items = get_items()
        self.item_id.choices = [(entry['item_id'], entry['item_name']) for entry in items]



class ModifyListing(FlaskForm):
    item_id = SelectField('Choose Item to Add Listing:', choices=[])
    quantity = StringField('Item Quantity')
    website = SelectField('Choose website listed on', choices=[('', ''), ('Etsy', 'Etsy'), ('Amazon', 'Amazon'), ('Ebay','Ebay')])
    listing_status = SelectField('Listing Status', choices=[('active', 'active'), ('sold','sold'), ('inactive', 'inactive')])
    listing_url = StringField('Paste url of listing below')
    unit_price = DecimalField('Listing Price Per Item:', places=2, rounding=None, validators=[DataRequired()])
    submit = SubmitField('Save')
    delete_button = SubmitField('Delete')

    # Get the latest items from the items table
    def __init__(self):
        super(ModifyListing, self).__init__()
        items = get_items()
        self.item_id.choices = [('','')] + [(entry['item_id'], entry['item_name']) for entry in items]


class RecordSale(FlaskForm):
    quantity = StringField('Quantity Sold')
    submit = SubmitField('Save')


class GenerateForecast(FlaskForm):
    item_id = SelectField('Choose Item to Run Forecast Report:', choices=[])
    submit = SubmitField('Run Report')

    # Get the latest items from the items table
    def __init__(self):
        super(GenerateForecast, self).__init__()
        items = get_items()
        self.item_id.choices = [(entry['item_id'], entry['item_name']) for entry in items]


class ShipItem(FlaskForm):
    sender_zip_code = StringField('Sender Zip Code', validators=[DataRequired(), Length(min=5, max=5)])
    sender_state = StringField('Sender State (2 Letter ID)', validators=[Length(min=2, max=2)])
    sender_city = StringField('Sender City')
    sender_street_address = StringField('Sender Street Address')
    sender_name = StringField('Sender Name')
    sender_phone = StringField('Sender Phone')

    recipient_zip_code = StringField('Recipient Zip Code', validators=[DataRequired(), Length(min=5, max=5)])
    recipient_state = StringField('Recipient State (2 Letter ID)', validators=[Length(min=2, max=2)])
    recipient_city = StringField('Recipient City')
    recipient_street_address = StringField('Recipient Street Address')
    recipient_name = StringField('Recipient Name')
    recipient_phone = StringField('Recipient Phone')

    item_weight = DecimalField('Item Weight in Pounds', validators=[DataRequired(), NumberRange(min=0.1)])
    package_length = IntegerField('Package Length in Inches', validators=[DataRequired(), NumberRange(min=1)])
    package_width = IntegerField('Package Width in Inches', validators=[DataRequired(), NumberRange(min=1)])
    package_height = IntegerField('Package Height in Inches', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Get Rates')

# Function to validate user search input. Returns True for valid input, False otherwise.
def check_input(input):
    regex = re.compile('[\\\@_!#$%^&*()<>/|}{~:]')
    if (regex.search(input) == None) and len(input) > 2:
        return True
    else:
        return False


def verify_positive_integer(input):
    try:
        converted_int = int(input)
        if converted_int > 0:
            return 'Valid'
        else:
            return 'Invalid input: Quantity should be greater than 0'
    except:
        return 'Invalid input: Quantity should be an integer'



# Landing page endpoint. Asks to enter an artist to search.
# On user input: validates user input, passes search term to API function, parses JSON, redirects to results page and passes variables needed to render page
@app.route("/about", methods=['GET', 'POST'])
@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def about():
    return render_template('about.html', title='About', posts=posts)


@app.route("/new_item", methods=['GET', 'POST'])
def new_item():

    # index controls which item to render on the page. If the index is 0, then add a new tag, else load contents of tag#
    index = request.args['index']
    image_files = []
    item_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(index))
    if os.path.exists(item_folder):
        image_files = [file for file in os.listdir(item_folder) if file.endswith(('.jpeg', '.png'))]

    if int(index) != 0:
        default_vals = get_items(index)
    form = ModifyItem()

    if request.method == "POST":     # When submitting data
        if form.submit.data:    # If submit button is pressed
            if form.validate_on_submit() and check_input(form.item_description.data):
                flash(f'Updates Submitted', 'success')
                item = {}
                item['item_id'] = index
                item['item_name'] = form.item_name.data
                item['item_description'] = form.item_description.data

                if int(index) != 0:     # If this is not a new item, use the update function
                    update_items(item)
                    img_id = str(index)
                else:
                    item_response = add_items(item)
                    img_id = item_response[1]


                if form.item_photo.data:
                    photo = form.item_photo.data
                    filename = secure_filename(photo.filename)
                    item_folder = os.path.join(app.config['UPLOAD_FOLDER'], img_id)

                    os.makedirs(item_folder, exist_ok=True)
                    photo.save(os.path.join(item_folder, filename))

                return redirect(url_for('items_list'))  # Update to items_list when this is built

        elif 'delete_image' in request.form:
            filename_to_delete = request.form['delete_image']
            file_path = os.path.join(item_folder, filename_to_delete)
            if os.path.exists(file_path):
                os.remove(file_path)
                flash("Image deleted successfully.", 'success')
                image_files = [file for file in os.listdir(item_folder) if file.endswith(('.jpeg', '.png'))]

        elif form.delete_button.data:
            # Checking if item has inventory associated. Item will not be deleted if associated with inventory
            inventory = get_inventory()
            for entry in inventory:
                if entry['item_id'] == int(index):
                    flash(f'Cannot delete item that has inventory allocated. Please delete inventory first.', 'danger')
                    return render_template('modify_items.html', form=form, index=index)
            delete_item(index)
            flash(f'Item Deleted', 'success')
            return redirect(url_for('items_list'))


    else:   # When first rendering the page (method = GET)
        if int(index) != 0:     #pre-populates the data if existing item is being modified
            form.item_name.data = default_vals[0]['item_name']
            form.item_description.data = default_vals[0]['item_description']

    return render_template('modify_items.html', form=form, index=index, image_files=image_files)


# Logic for rendering list of items with modification link:
@app.route("/items_list", methods=['GET', 'POST'])
def items_list():
    items = get_items()
    return render_template('items_list.html', json_data=items)


@app.route("/modify_inventory", methods=['GET', 'POST'])
def modify_inventory():

    # index controls which item to render on the page. If the index is 0, then add a new tag, else load contents of tag#
    index = request.args['index']
    if int(index) != 0:
        default_vals = get_inventory(index)
    form = ModifyInventory()

    if request.method == "POST":     # When submitting data
        if form.submit.data:    # If submit button is pressed
            if form.validate_on_submit():
                quantity_check = verify_positive_integer(form.quantity.data)
                if quantity_check == 'Valid':
                    flash(f'Updates Submitted', 'success')
                    inventory_entry = {}
                    inventory_entry['inventory_id'] = index
                    inventory_entry['item_id'] = int(form.item_id.data)
                    inventory_entry['quantity'] = int(form.quantity.data)
                    inventory_entry['unit_price'] = float(form.unit_price.data)
                    inventory_entry['location_string'] = form.location_string.data
                else:
                    flash(quantity_check, 'danger')
                    return render_template('modify_inventory.html', form=form)

                if int(index) != 0:     # If this is not a new item, use the update function
                    update_inventory(inventory_entry)
                else:
                    add_inventory(inventory_entry)  # If this is a new item, use the add function

                return redirect(url_for('inventory_list'))  # Update to items_list when this is built
        elif form.delete_button.data:
            delete_inventory(index)
            flash(f'Inventory Deleted', 'success')
            return redirect(url_for('inventory_list'))

    else:   # When first rendering the page (method = GET)
        if int(index) != 0:     #pre-populates the data if existing item is being modified
            form.item_id.data = str(default_vals[0]['item_id'])
            form.location_string.data = default_vals[0]['location_string']
            form.quantity.data = default_vals[0]['quantity']
            form.unit_price.data = default_vals[0]['unit_price']

    return render_template('modify_inventory.html', form=form)


# Logic for rendering list of inventory with modification link. Brings in latest item_name from the items table.
@app.route("/inventory_list", methods=['GET', 'POST'])
def inventory_list():
    inventory = get_inventory()     # Retrieving all data from inventory database
    items = get_items()     # Retrieving all data from the items database

    if len(inventory) > 0:  # Verifying there are entries in inventory table, else return blank list
        df_inventory = pd.DataFrame(inventory)  # Converting inventory and Items to DataFrames to join
        df_items = pd.DataFrame(items)

        df_merge = pd.merge(df_inventory, df_items, how='inner', on='item_id')  # Joining to bring in item_name

        df_merge = df_merge[['inventory_id', 'item_id', 'item_name', 'quantity', 'location_string']]    # Reducing to just necessary columns
        json_output = df_merge.to_dict(orient='records')

    else:
        json_output = []

    return render_template('inventory_list.html', json_data=json_output)


@app.route("/download_inventory_csv")
def download_inventory_csv():
    inventory = get_inventory()  # Retrieving all data from inventory database
    items = get_items()  # Retrieving all data from the items database


    if len(inventory) == 0 or len(items) == 0:  # Verifying there are entries in inventory table, else return blank list
        df_merge = pd.DataFrame(columns=['inventory_id', 'item_id', 'item_name', 'quantity', 'location_string'])

    else:
        df_inventory = pd.DataFrame(inventory)  # Converting inventory and Items to DataFrames to join
        df_items = pd.DataFrame(items)

        df_merge = pd.merge(df_inventory, df_items, how='inner', on='item_id')  # Joining to bring in item_name

        df_merge = df_merge[['inventory_id', 'item_id', 'item_name', 'quantity',
                             'location_string']]  # Reducing to just necessary columns

    # Creating an in-memory .csv
    output = BytesIO()
    df_merge.to_csv(output, index=False)
    output.seek(0)

    # Getting today's date and time and appending to file name
    time_string = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_filename = f'inventory_download_{time_string}.csv'

    return send_file(output,
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name=output_filename)


@app.route("/uploads/<index>/<filename>")
def uploaded_file(filename, index):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], str(index)), filename)


@app.route("/manage_listings")
def manage_listings():
    listings = get_listings()     # Retrieving all data from inventory database
    items = get_items()     # Retrieving all data from the items database

    if len(listings) > 0:  # Verifying there are entries in inventory table, else return blank list
        df_listings = pd.DataFrame(listings)  # Converting inventory and Items to DataFrames to join
        df_items = pd.DataFrame(items)

        df_merge = pd.merge(df_listings, df_items, how='inner', on='item_id')  # Joining to bring in item_name

        df_merge = df_merge[['listing_id', 'item_id', 'item_name', 'quantity', 'website', 'listing_url', 'listing_status']]    # Reducing to just necessary columns
        json_output = df_merge.to_dict(orient='records')

    else:
        json_output = []

    return render_template('manage_listings.html', json_data=json_output)


@app.route("/modify_listing", methods=['GET', 'POST'])
def modify_listing():
    # index controls which item to render on the page. If the index is 0, then add a new entry, else load contents of existing entry
    index = request.args['index']
    if int(index) != 0:
        default_vals = get_listings(index)
    form = ModifyListing()

    if request.method == "POST":     # When submitting data
        if form.submit.data:    # If submit button is pressed
            if form.validate_on_submit():
                quantity_check = verify_positive_integer(form.quantity.data)
                if quantity_check == 'Valid':
                    flash(f'Updates Submitted', 'success')
                    listing_entry = {}
                    listing_entry['listing_id'] = int(index)
                    listing_entry['item_id'] = int(form.item_id.data)
                    listing_entry['quantity'] = int(form.quantity.data)
                    listing_entry['website'] = form.website.data
                    listing_entry['listing_status'] = form.listing_status.data
                    listing_entry['listing_url'] = form.listing_url.data
                    listing_entry['unit_price'] = float(form.unit_price.data)

                else:
                    flash(quantity_check, 'danger')
                    return render_template('modify_inventory.html', form=form)

                if int(index) != 0:     # If this is not a new item, use the update function
                    update_listing(listing_entry)
                else:
                    add_listing(listing_entry)  # If this is a new item, use the add function

                return redirect(url_for('manage_listings'))  # Update to items_list when this is built
        elif form.delete_button.data:
            delete_listing(index)
            flash(f'Inventory Deleted', 'success')
            return redirect(url_for('manage_listings'))

    else:   # When first rendering the page (method = GET)
        if int(index) != 0:     #pre-populates the data if existing item is being modified
            form.item_id.data = str(default_vals[0]['item_id'])
            form.quantity.data = default_vals[0]['quantity']
            form.website.data = default_vals[0]['website']
            form.listing_status.data = default_vals[0]['listing_status']
            form.listing_url.data = default_vals[0]['listing_url']
            form.unit_price.data = default_vals[0]['unit_price']

    return render_template('modify_listing.html', form=form)


@app.route("/record_sale", methods=['GET', 'POST'])
def record_sale():
    form = RecordSale()
    index = request.args['index']
    listings = get_listings(index)     # Retrieving listing from database

    if request.method == "POST":     # When submitting data
        if form.submit.data:    # If submit button is pressed
            if int(form.quantity.data) > listings[0]['quantity']:
                flash('Quantity cannot exceed listing quantity', 'danger')
                return render_template('record_sale.html', form=form)
            else:
                record_sale_in_db(listings[0], form.quantity.data)
                return redirect(url_for('manage_listings'))

    return render_template('record_sale.html', form=form)


@app.route("/report_select", methods=['GET', 'POST'])
def report_select():
    form = GenerateForecast()
    report_type = request.args['report']

    if request.method == 'POST':
        # print(report_type)
        if report_type == 'profit_report':
            return redirect(url_for('profit_report', item=form.item_id.data))
        elif report_type == 'inventory_report':
            return redirect(url_for('inventory_report', item=form.item_id.data))
        elif report_type == 'sales_forecast':
            return redirect(url_for('sales_forecast', item=form.item_id.data))

    return render_template('report_select.html', form=form)


@app.route("/profit_report", methods=['GET', 'POST'])
def profit_report():
    index = request.args['item']
    sales_data = get_sales(int(index))
    plot_html = generate_profit_report(sales_data)
    return render_template('profit_report.html',  plot_html=plot_html)


@app.route("/inventory_report", methods=['GET', 'POST'])
def inventory_report():
    index = request.args['item']

    current_inventory = get_inventory()
    current_inventory = [record for record in current_inventory if record['item_id'] == int(index)]

    inventory_transactions = get_inventory_history()
    inventory_transactions = [record for record in inventory_transactions if record['item_id'] == int(index)]

    plot_html = generate_inventory_history(current_inventory=current_inventory, inventory_history=inventory_transactions)
    return render_template('inventory_report.html', plot_html=plot_html)


@app.route("/sales_forecast", methods=['GET', 'POST'])
def sales_forecast():
    index = request.args['item']
    forecast_data = get_sales(int(index))
    plot_html = create_forecast_plot_html(forecast_data)
    return render_template('sales_forecast.html', plot_html=plot_html)


@app.route("/ship_item", methods=['GET', 'POST'])
def ship_item():
    form = ShipItem()
    parsed_rates = None  # Initialize to None

    if request.method == "POST":  # When submitting data
        if form.validate_on_submit():
            sender_zip_code = form.sender_zip_code.data
            recipient_zip_code = form.recipient_zip_code.data
            package_weight = form.item_weight.data
            package_length = form.package_length.data
            package_height = form.package_height.data
            package_width = form.package_width.data

            fed_ex_access_token = get_access_token()

            raw_rates = get_rates_and_transit_times(
                access_token=fed_ex_access_token,
                sender_zip_code=sender_zip_code,
                recipient_zip_code=recipient_zip_code,
                package_weight=package_weight,
                package_length=package_length,
                package_width=package_width,
                package_height=package_height
            )

            parsed_rates = parse_rate_response(raw_rates)


    return render_template('ship_item.html', form=form, parsed_rates=parsed_rates)


@app.route("/print_label", methods=['POST'])
def print_label():

    sender_zip_code = request.form.get("sender_zip_code")
    sender_city = request.form.get("sender_city")
    sender_state = request.form.get("sender_state")
    sender_street_address = request.form.get("sender_street_address")
    sender_name = request.form.get("sender_name")
    sender_phone = request.form.get("sender_phone")

    recipient_zip_code = request.form.get("recipient_zip_code")
    recipient_city = request.form.get("recipient_city")
    recipient_state = request.form.get("recipient_state")
    recipient_street_address = request.form.get("recipient_street_address")
    recipient_name = request.form.get("recipient_name")
    recipient_phone = request.form.get("recipient_phone")

    item_weight = float(request.form.get("item_weight"))
    package_length = int(request.form.get("package_length"))
    package_width = int(request.form.get("package_width"))
    package_height = int(request.form.get("package_height"))

    selected_option = {
        "ServiceType": request.form.get("service_type"),
        "ServiceName": request.form.get("service_name"),
        "TotalNetCharge": float(request.form.get("total_cost")),
        "SaturdayDelivery": request.form.get("saturday_delivery") == "True",
        "EstimatedDelivery": request.form.get("estimated_delivery")
    }

    # print(str(request.form.get("sender_zip_code")))

    # Use these details to call the generate_shipping_label function
    # Ensure you have the sender, recipient, and package details ready
    fed_ex_access_token = get_access_token()

    shipper = {
        "address": {
            "postalCode": str(sender_zip_code),
            "countryCode": "US",
            "stateOrProvinceCode": str(sender_state),
            "city": str(sender_city),
            "streetLines": [str(sender_street_address)],
            "residential": False
        },
        "contact": {
            "personName": str(sender_name),
            "phoneNumber": str(sender_phone)
        }
    }

    recipient = {
        "address": {
            "postalCode": str(recipient_zip_code),
            "countryCode": "US",
            "stateOrProvinceCode": str(recipient_state),
            "city": str(recipient_city),
            "streetLines": [str(recipient_street_address)],
            "residential": True
        },
        "contact": {
            "personName": str(recipient_name),
            "phoneNumber": str(recipient_phone)
        }
    }

    package_details = {
        "weight": {
            "units": "LB",
            "value": str(item_weight)
        },
        "dimensions": {
            "length": str(package_length),
            "width": str(package_width),
            "height": str(package_height),
            "units": "IN"
        }
    }

    label_file_path = "shipping_label.pdf"

    try:
        confirmation = generate_shipping_label(
            access_token=fed_ex_access_token,
            selected_option=selected_option,
            shipper=shipper,
            recipient=recipient,
            package_details=package_details,
            label_file_path=label_file_path
        )

        # Return the generated label as a downloadable file
        return send_file(label_file_path, as_attachment=True)

    except Exception as e:
        return f"An error occurred while generating the label: {str(e)}"



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3839, debug=True, threaded=True)  # Flask WSGI dev mode
