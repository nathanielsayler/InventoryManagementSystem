# This file contains all input/output functions for interacting with the database

import sqlite3
import pathlib

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

    try:
        cur = conn.cursor()
        print(inventory_entry)
        cur.execute("INSERT INTO INVENTORY (quantity, item_id, location_string) VALUES (?, ?, ?)", (inventory_entry['quantity'], inventory_entry['item_id'], inventory_entry['location_string']))
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


# Updates existing inventory entry in inventory table
def update_inventory(inventory, db_file=None):
    updated_inventory = {}
    try:
        conn = create_connection(db_file)
        cur = conn.cursor()
        cur.execute("update INVENTORY SET quantity = ?, item_id= ?, location_string = ?  WHERE inventory_id = ?",
                    (inventory["quantity"], inventory['item_id'], inventory['location_string'], inventory['inventory_id'],))
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
        cur.execute("INSERT INTO LISTINGS (item_id, quantity, website, listing_url, listing_status) VALUES (?, ?, ?, ?, ?)", (listing_entry['item_id'], listing_entry['quantity'], listing_entry['website'], listing_entry['listing_url'], listing_entry['listing_status']))
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
        cur.execute("update LISTINGS SET item_id = ?, quantity = ?, website = ?, listing_url = ?, listing_status = ? WHERE listing_id = ?",
                    (listing["item_id"], listing["quantity"], listing['website'], listing['listing_url'], listing['listing_status'], listing['listing_id'],))
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

