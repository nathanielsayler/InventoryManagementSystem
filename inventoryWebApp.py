import pandas as pd
from flask import Flask, render_template, url_for, flash, redirect, request, json, send_file, send_from_directory
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.utils import secure_filename
from wtforms import SubmitField, StringField, TextAreaField, SelectField
import re
from io import BytesIO
from datetime import datetime
import os

from inventoryDbFunctions import get_items, add_items, delete_item, update_items
from inventoryDbFunctions import get_inventory, add_inventory, delete_inventory, update_inventory
from inventoryDbFunctions import get_listings, add_listing, delete_listing, update_listing

# This .py file contains code to run web application. Renders all .html pages through Flask, flask_wtf, and wtforms packages.

# Flask Web App configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = '472bcf297c23d31e924ec24b'
app.config['UPLOAD_FOLDER'] = 'images/'

posts = [
    {
        'author': 'Nathan Sayler',
        'title': 'How to Use this Application',
        'content': '''Instructions for using each feature will be documented here as they are developed.''',
        'date_posted': '09/15/24'
    }
]


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
    submit = SubmitField('Save')
    delete_button = SubmitField('Delete')

    # Get the latest items from the items table
    def __init__(self):
        super(ModifyListing, self).__init__()
        items = get_items()
        self.item_id.choices = [('','')] + [(entry['item_id'], entry['item_name']) for entry in items]



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
            print(default_vals)
            form.item_id.data = str(default_vals[0]['item_id'])
            form.location_string.data = default_vals[0]['location_string']
            form.quantity.data = default_vals[0]['quantity']

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
    print(listings)
    items = get_items()     # Retrieving all data from the items database
    print(items)

    if len(listings) > 0:  # Verifying there are entries in inventory table, else return blank list
        df_listings = pd.DataFrame(listings)  # Converting inventory and Items to DataFrames to join
        df_items = pd.DataFrame(items)

        df_merge = pd.merge(df_listings, df_items, how='inner', on='item_id')  # Joining to bring in item_name

        df_merge = df_merge[['listing_id', 'item_id', 'item_name', 'quantity', 'website', 'listing_url', 'listing_status']]    # Reducing to just necessary columns
        json_output = df_merge.to_dict(orient='records')
        print(json_output)

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

                else:
                    flash(quantity_check, 'danger')
                    return render_template('modify_inventory.html', form=form)

                if int(index) != 0:     # If this is not a new item, use the update function
                    update_listing(listing_entry)
                else:
                    add_listing(listing_entry)  # If this is a new item, use the add function
                    print(listing_entry)

                return redirect(url_for('manage_listings'))  # Update to items_list when this is built
        elif form.delete_button.data:
            delete_listing(index)
            flash(f'Inventory Deleted', 'success')
            return redirect(url_for('manage_listings'))

    else:   # When first rendering the page (method = GET)
        if int(index) != 0:     #pre-populates the data if existing item is being modified
            print(default_vals)
            form.item_id.data = str(default_vals[0]['item_id'])
            form.quantity.data = default_vals[0]['quantity']
            form.website.data = default_vals[0]['website']
            form.listing_status.data = default_vals[0]['listing_status']
            form.listing_url.data = default_vals[0]['listing_url']

    return render_template('modify_listing.html', form=form)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3839, debug=True, threaded=True)  # Flask WSGI dev mode
