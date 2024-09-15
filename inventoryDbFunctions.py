# This file contains all input/output functions for interacting with the database

import sqlite3
import pathlib

Default_Directory = pathlib.Path().absolute()
Default_Directory = str(Default_Directory)
global db_file
db_file = Default_Directory+"\\db\\inventory.sqlite"


# Creates a connection to a SQLite database
def create_connection():
    conn2 = sqlite3.connect(db_file)
    return conn2


# Items Functions

# function to return a specific item entry when key is passed, else return all items
def get_items(item_id=0):
    items = []
    try:
        conn = create_connection()
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
def add_items(item):
    inserted_item = {}
    conn = sqlite3.connect(db_file)
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO ITEMS (item_name, item_description) VALUES (?, ?)", (item['item_name'], item['item_description']))
        conn.commit()
        conn.close()
        #inserted_item = get_items(cur.lastrowid)
    except:
        print("Error encountered when trying to insert new item into database.")
        conn.rollback()

    finally:
        conn.close()

    return inserted_item


# Updates existing item entry in items table
def update_items(item):
    updated_item = {}
    try:
        conn = create_connection()
        cur = conn.cursor()
        cur.execute("update ITEMS SET item_name = ?, item_description = ? WHERE item_id = ?",
                    (item["item_name"], item['item_description'],))
        conn.commit()
        conn.close()
    except:
        print("Error updating entry in items table")
        conn.rollback()
        updated_item = {}
    finally:
        conn.close()

    return updated_item


# deletes item from items table
def delete_item(item_id):
    message = {}
    try:
        conn = create_connection()
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
def get_inventory(inventory_id=0):
    inventory_entries = []
    try:
        conn = create_connection()
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
def add_inventory(inventory_entry):
    inserted_item = {}
    print(inventory_entry)
    conn = sqlite3.connect(db_file)

    try:
        cur = conn.cursor()
        print(inventory_entry)
        cur.execute("INSERT INTO INVENTORY (quantity, item_id, location_string) VALUES (?, ?, ?)", (inventory_entry['quantity'], inventory_entry['item_id'], inventory_entry['location_string']))
        conn.commit()
        conn.close()
        #inserted_item = get_items(cur.lastrowid)
    except:
        print("Error encountered when trying to insert new inventory entry into database.")
        conn.rollback()

    finally:
        conn.close()

    return inserted_item


# Updates existing inventory entry in inventory table
def update_inventory(inventory):
    updated_inventory = {}
    try:
        conn = create_connection()
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
def delete_inventory(inventory_id):
    message = {}
    try:
        conn = create_connection()
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

