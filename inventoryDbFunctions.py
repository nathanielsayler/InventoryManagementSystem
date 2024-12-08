# This file contains all input/output functions for interacting with the database

import sqlite3
import pathlib
from datetime import datetime

Default_Directory = pathlib.Path().absolute()
Default_Directory = str(Default_Directory)
prod_db_file = Default_Directory+"\\db\\inventory.sqlite"


# Creates a connection to a SQLite database
def create_connection(db_file=None):
    if db_file:
        print(db_file)
    else:
        db_file = prod_db_file
    conn2 = sqlite3.connect(db_file)
    return conn2


# Items Functions

# function to return a specific item entry when key is passed, else return all items
def get_items(item_id=0, db_file=None):
    items = []
    try:
        conn = create_connection(db_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if item_id == 0:
            cur.execute("SELECT * FROM ITEMS")
        else:
            id_str = str(item_id)
            cur.execute("SELECT * FROM ITEMS WHERE item_id = " + id_str)
        rows = cur.fetchall()

        # convert row objects to dictionary
        for i in rows:
            item = {}
            item["item_id"] = i["item_id"]
            item["item_name"] = i["item_name"]
            item["item_description"] = i["item_description"]
            items.append(item)

        conn.close()

    except:
        print("Error in get_items function")

    return items


# Adds a new item to the items table
def add_items(item, db_file=None):
    conn = create_connection(db_file)
    error_message = ''
    new_id = ''
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO ITEMS (item_name, item_description) VALUES (?, ?)",
                    (item['item_name'], item['item_description']))

        new_id = str(cur.lastrowid)
        conn.commit()
        conn.close()
    except:
        #print("Error encountered when trying to insert new item into database.")
        conn.rollback()
        error_message = 'Error adding record to database.'

    finally:
        conn.close()

    return [error_message, new_id]


# Updates existing item entry in items table
def update_items(item, db_file=None):
    updated_item = {}
    try:
        conn = create_connection(db_file)
        cur = conn.cursor()
        cur.execute("update ITEMS SET item_name = ?, item_description = ? WHERE item_id = ?",
                    (item["item_name"], item['item_description'], item['item_id']))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error updating entry in items table: ", e)
        conn.rollback()
        updated_item = {}
    finally:
        conn.close()

    return updated_item


# deletes item from items table
def delete_item(item_id, db_file=None):
    message = {}
    try:
        conn = create_connection(db_file)
        conn.execute("DELETE from ITEMS WHERE item_id = ?", (item_id,))
        conn.commit()
        conn.close()
        message["status"] = "Item deleted successfully"
    except:
        conn.rollback()
        message["status"] = "Could not delete item"
    finally:
        conn.close()

    return message


# Inventory Functions

# function to return a specific inventory entry when key is passed, else return all inventory entries
def get_inventory(inventory_id=0, db_file=None):
    inventory_entries = []
    try:
        conn = create_connection(db_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if inventory_id == 0:
            cur.execute("SELECT * FROM INVENTORY")
        else:
            id_str = str(inventory_id)
            cur.execute("SELECT * FROM INVENTORY WHERE inventory_id = " + id_str)
        rows = cur.fetchall()

        # convert row objects to dictionary
        for i in rows:
            inventory_entry = {}
            inventory_entry["inventory_id"] = i["inventory_id"]
            inventory_entry["quantity"] = i["quantity"]
            inventory_entry["item_id"] = i["item_id"]
            inventory_entry["location_string"] = i["location_string"]
            inventory_entry['unit_price'] = i["unit_price"]
            inventory_entries.append(inventory_entry)

        conn.close()

    except:
        print("Error in get_inventory function")

    return inventory_entries


# Adds a new entry to the inventory table
def add_inventory(inventory_entry, db_file=None):
    inserted_item = {}
    print(inventory_entry)
    conn = create_connection(db_file)
    error_message = ''
    inventory = get_inventory()
    if len(inventory) > 0 and 'location_string' in inventory_entry:
        filtered_inventory = [entry for entry in inventory if entry.get('location_string') == inventory_entry['location_string']]
        filtered_inventory = [entry for entry in filtered_inventory if entry.get('item_id') == inventory_entry['item_id']]
    else:
        filtered_inventory = []

    # Logic for "netting". If inventory entry exists, add the new entry to that and recalculate avg cost
    if len(filtered_inventory) > 0:
        filtered_inventory.append(inventory_entry)
        total_quantity = sum(entry['quantity'] for entry in filtered_inventory)
        avg_cost = sum(entry['unit_price'] * entry['quantity'] for entry in filtered_inventory) / total_quantity
        final_record = filtered_inventory[0]
        final_record['unit_price'] = round(avg_cost, 2)
        final_record['quantity'] = total_quantity
        update_inventory(final_record)

    else:
        try:
            cur = conn.cursor()
            print(inventory_entry)
            cur.execute("INSERT INTO INVENTORY (quantity, item_id, location_string, unit_price) VALUES (?, ?, ?, ?)", (inventory_entry['quantity'], inventory_entry['item_id'], inventory_entry['location_string'], inventory_entry['unit_price']))
            conn.commit()
            conn.close()

            new_record_id = cur.lastrowid

            conn = create_connection(db_file)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO INVENTORY_TRANSACTIONS (item_id, inventory_id, qty_change, date) VALUES (?, ?, ?, ?)", (
                    inventory_entry['item_id'], new_record_id, inventory_entry['quantity'], datetime.today().strftime("%m-%d-%Y")))
            conn.commit()
            conn.close()

            #inserted_item = get_items(cur.lastrowid)
        except Exception as e:
            #print("Error encountered when trying to insert new inventory entry into database.")
            conn.rollback()
            error_message = 'Error adding record to database.'
            print(e)

        finally:
            conn.close()

    return error_message


# Updates existing inventory entry in inventory table
def update_inventory(inventory, db_file=None):
    updated_inventory = {}

    # Record inventory transaction in transactions table
    prior_record = get_inventory(inventory['inventory_id'])[0]
    prior_qty = prior_record['quantity']
    if prior_qty != inventory['quantity']:
        qty_change = inventory['quantity'] - prior_qty
        try:
            conn = create_connection(db_file)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO INVENTORY_TRANSACTIONS (item_id, inventory_id, qty_change, date) VALUES (?, ?, ?, ?)", (
                inventory['item_id'], inventory['inventory_id'], qty_change, datetime.today().strftime("%m-%d-%Y")))
            conn.commit()
            conn.close()

        except Exception as e:
            conn.rollback()
            error_message = 'Error adding record to database.'
            print(e)

        finally:
            conn.close()



    try:
        conn = create_connection(db_file)
        cur = conn.cursor()
        cur.execute("update INVENTORY SET quantity = ?, item_id= ?, location_string = ?, unit_price = ?  WHERE inventory_id = ?",
                    (inventory["quantity"], inventory['item_id'], inventory['location_string'], inventory['unit_price'], inventory['inventory_id'],))
        conn.commit()
        conn.close()
    except:
        print("Error updating entry in inventory table")
        conn.rollback()
        updated_item = {}
    finally:
        conn.close()

    return updated_inventory


# deletes inventory entry from inventory table
def delete_inventory(inventory_id, db_file=None):
    message = {}
    try:
        conn = create_connection(db_file)
        conn.execute("DELETE from INVENTORY WHERE inventory_id = ?", (inventory_id,))
        conn.commit()
        conn.close()
        message["status"] = "Item deleted successfully"
    except:
        conn.rollback()
        message["status"] = "Could not delete item"
    finally:
        conn.close()

    return message


# Retrieve all the listings from the listings table
def get_listings(listing_id=0, db_file=None):
    listing_entries = []
    try:
        conn = create_connection(db_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if listing_id == 0:
            cur.execute("SELECT * FROM LISTINGS")
        else:
            id_str = str(listing_id)
            cur.execute("SELECT * FROM LISTINGS WHERE listing_id = " + id_str)
        rows = cur.fetchall()

        # convert row objects to dictionary
        for i in rows:
            listing_entry = {}
            listing_entry["listing_id"] = i["listing_id"]
            listing_entry["item_id"] = i["item_id"]
            listing_entry["quantity"] = i["quantity"]
            listing_entry["website"] = i["website"]
            listing_entry["listing_url"] = i["listing_url"]
            listing_entry["listing_status"] = i["listing_status"]
            listing_entry["unit_price"] = i["unit_price"]
            listing_entries.append(listing_entry)

        conn.close()

    except:
        print("Error in get_listings function")

    return listing_entries


# Adds a new entry to the listings table
def add_listing(listing_entry, db_file=None):
    inserted_listing = {}
    print(listing_entry)
    conn = create_connection(db_file)
    error_message = ''

    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO LISTINGS (item_id, quantity, website, listing_url, listing_status, unit_price) VALUES (?, ?, ?, ?, ?, ?)", (listing_entry['item_id'], listing_entry['quantity'], listing_entry['website'], listing_entry['listing_url'], listing_entry['listing_status'], listing_entry['unit_price']))
        conn.commit()
        conn.close()
        #inserted_item = get_items(cur.lastrowid)
    except:
        #print("Error encountered when trying to insert new inventory entry into database.")
        conn.rollback()
        error_message = 'Error adding record to database.'

    finally:
        conn.close()

    return error_message


# Updates existing listing entry in listings table
def update_listing(listing, db_file=None):
    updated_listing = {}
    print(listing)
    try:
        conn = create_connection(db_file)
        cur = conn.cursor()
        cur.execute("update LISTINGS SET item_id = ?, quantity = ?, website = ?, listing_url = ?, listing_status = ?, unit_price = ? WHERE listing_id = ?",
                    (listing["item_id"], listing["quantity"], listing['website'], listing['listing_url'], listing['listing_status'], listing['unit_price'], listing['listing_id'],))
        conn.commit()
        conn.close()
    except:
        print("Error updating entry in listings table")
        conn.rollback()
        updated_listing = {}
    finally:
        conn.close()

    return updated_listing


# deletes inventory entry from inventory table
def delete_listing(listing_id, db_file=None):
    message = {}
    try:
        conn = create_connection(db_file)
        conn.execute("DELETE from LISTINGS WHERE listing_id = ?", (listing_id,))
        conn.commit()
        conn.close()
        message["status"] = "Item deleted successfully"
    except:
        conn.rollback()
        message["status"] = "Could not delete item"
    finally:
        conn.close()

    return message


# This function updates the listing status and quantity when an item is marked as sold. It also records the sale.
def record_sale_in_db(listing, quantity):
    if listing['quantity'] == int(quantity):
        listing['listing_status'] = 'sold'

    listing['quantity'] = listing['quantity'] - int(quantity)   # Setting new quantity
    update_listing(listing)

    # Creating Sales record
    record = {}
    record['quantity'] = quantity
    record['item_id'] = listing['item_id']
    record['sale_price'] = listing['unit_price']
    record['date_sold'] = datetime.today().strftime("%m-%d-%Y")

    inventory = get_inventory()
    filtered_inventory = [entry for entry in inventory if entry.get('item_id') == listing['item_id']]
    if len(filtered_inventory) == 0:
        record['acquisition_cost'] = 0
    else:
        record['acquisition_cost'] = filtered_inventory[0]['unit_price']

    # Writing Sales record to db
    conn = create_connection(None)
    error_message = ''
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO SALES (item_id, quantity, sale_price, acquisition_cost, date_sold) VALUES (?, ?, ?, ?, ?)",
            (record['item_id'], record['quantity'], record['sale_price'],
             record['acquisition_cost'], record['date_sold']))
        conn.commit()
        conn.close()
    except Exception as e:
        print(e)
        conn.rollback()
        error_message = 'Error adding record to database.'

    finally:
        conn.close()

    print(record)


# function to return a specific inventory entry when key is passed, else return all inventory entries
def get_sales(item_id=0, db_file=None):
    sales_entries = []
    try:
        conn = create_connection(db_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if item_id == 0:
            cur.execute("SELECT * FROM SALES")
        else:
            id_str = str(item_id)
            cur.execute("SELECT * FROM SALES WHERE item_id = " + id_str)
        rows = cur.fetchall()

        # convert row objects to dictionary
        for i in rows:
            sale_entry = {}
            sale_entry["sale_id"] = i["sale_id"]
            sale_entry["item_id"] = i["item_id"]
            sale_entry["quantity"] = i["quantity"]
            sale_entry["sale_price"] = i["sale_price"]
            sale_entry["acquisition_cost"] = i["acquisition_cost"]
            sale_entry["date_sold"] = i["date_sold"]
            sales_entries.append(sale_entry)

        conn.close()

    except:
        print("Error in get_inventory function")

    return sales_entries


# function to return a specific inventory entry when key is passed, else return all inventory entries
def get_inventory_history(inventory_id=0, db_file=None):
    inventory_transaction_entries = []
    try:
        conn = create_connection(db_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if inventory_id == 0:
            cur.execute("SELECT * FROM INVENTORY_TRANSACTIONS")
        else:
            id_str = str(inventory_id)
            cur.execute("SELECT * FROM INVENTORY_TRANSACTIONS WHERE inventory_id = " + id_str)
        rows = cur.fetchall()

        # convert row objects to dictionary
        for i in rows:
            inventory_entry = {}
            inventory_entry["inventory_transaction_id"] = i["inventory_transaction_id"]
            inventory_entry["item_id"] = i["item_id"]
            inventory_entry["inventory_id"] = i["inventory_id"]
            inventory_entry["qty_change"] = i["qty_change"]
            inventory_entry['date'] = i["date"]
            inventory_transaction_entries.append(inventory_entry)

        conn.close()

    except:
        print("Error in get_inventory function")

    return inventory_transaction_entries
