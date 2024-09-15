import pandas as pd
from flask import Flask, render_template, url_for, flash, redirect, request, json
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField, SelectField
import re

from inventoryDbFunctions import get_items, add_items, delete_item, update_items
from inventoryDbFunctions import get_inventory, add_inventory, delete_inventory, update_inventory

# This .py file contains code to run web application. Renders all .html pages through Flask, flask_wtf, and wtforms packages.

# Flask Web App configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = '472bcf297c23d31e924ec24b'

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
    item_name = StringField('Enter Name of New Item')
    item_description = TextAreaField('Enter Item Description')
    submit = SubmitField('Save')
    delete_button = SubmitField('Delete')


class ModifyInventory(FlaskForm):
    items = get_items()
    print(items)
    choices = [(entry['item_id'], entry['item_name']) for entry in items]
    item_id = SelectField('Choose Item to Add Inventory:', choices=choices)
    quantity = StringField('Enter Item Quantity')
    location_string = StringField("Enter item locator string:")
    submit = SubmitField('Save')
    delete_button = SubmitField('Delete')


# Function to validate user search input. Returns True for valid input, False otherwise.
def check_input(input):
    regex = re.compile('[\\\@_!#$%^&*()<>/|}{~:]')
    if (regex.search(input) == None) and len(input) > 2:
        return True
    else:
        return False


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
                else:
                    add_items(item)

                return redirect(url_for('items_list'))  # Update to items_list when this is built
        elif form.delete_button.data:
            delete_item(index)
            return redirect(url_for('items_list'))


    else:   # When first rendering the page (method = GET)
        if int(index) != 0:     #pre-populates the data if existing item is being modified
            form.item_name.data = default_vals[0]['item_name']
            form.item_description.data = default_vals[0]['item_description']

    return render_template('modify_items.html', form=form)


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
                flash(f'Updates Submitted', 'success')
                inventory_entry = {}
                inventory_entry['inventory_id'] = index
                inventory_entry['item_id'] = int(form.item_id.data)
                inventory_entry['quantity'] = int(form.quantity.data)
                inventory_entry['location_string'] = form.location_string.data

                if int(index) != 0:     # If this is not a new item, use the update function
                    update_inventory(inventory_entry)
                else:
                    add_inventory(inventory_entry)

                return redirect(url_for('inventory_list'))  # Update to items_list when this is built
        elif form.delete_button.data:
            delete_inventory(index)
            return redirect(url_for('inventory_list'))

    else:   # When first rendering the page (method = GET)
        if int(index) != 0:     #pre-populates the data if existing item is being modified
            print(default_vals)
            form.item_id.data = str(default_vals[0]['item_id'])
            form.location_string.data = default_vals[0]['location_string']
            form.quantity.data = default_vals[0]['quantity']

    return render_template('modify_inventory.html', form=form)


# Logic for rendering list of inventory with modification link:
@app.route("/inventory_list", methods=['GET', 'POST'])
def inventory_list():
    items = get_inventory()
    return render_template('inventory_list.html', json_data=items)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3839, debug=True, threaded=True)  # Flask WSGI dev mode
