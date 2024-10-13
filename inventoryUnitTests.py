import sqlite3
import unittest
import pathlib

from inventoryDbFunctions import create_connection, add_items, get_items, add_inventory, get_inventory
import inventoryWebApp

Default_Directory = pathlib.Path().absolute()
Default_Directory = str(Default_Directory)
#global db_file_test
db_file_test = Default_Directory+"\\db\\test_db.sqlite"



class TestAddItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):    # Creates the Items table if it doesn't already exist in Test DB, and removes record for valid test if it exists
        cls.conn = create_connection(db_file_test)
        cls.cur = cls.conn.cursor()
        cls.cur.execute('''
            CREATE TABLE IF NOT EXISTS items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            item_description TEXT
            );
        ''')


        item = {'item_name': 'Test 1 Item', 'item_description': 'Test 1 Description'}
        cls.cur.execute("DELETE FROM items WHERE item_name = ? AND item_description = ?",
                        (item['item_name'], item['item_description']))

        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_add_item_valid(self):
        item = {'item_name': 'Test 1 Item', 'item_description': 'Test 1 Description'}
        error_message = add_items(item, db_file=db_file_test)[0]

        self.cur.execute("SELECT * FROM items WHERE item_name = ? AND item_description = ?",
                         (item['item_name'], item['item_description']))
        result = self.cur.fetchone()

        self.assertIsNotNone(result, "The item was not added to the database.")
        self.assertEqual(error_message, '','The function did not return an empty string')

    def test_add_item_without_name(self):
        item = {'item_description': 'Test 2 Description'}

        self.cur.execute("SELECT COUNT(*) FROM items")  # getting record count before insert
        count1 = self.cur.fetchone()[0]

        error_message = add_items(item, db_file=db_file_test)[0]   # Executing function

        self.cur.execute("SELECT COUNT(*) FROM items")
        count2 = self.cur.fetchone()[0]

        self.assertEqual(count1, count2, 'A record was unexpectedly inserted')
        self.assertEqual(error_message, 'Error adding record to database.', 'Error message did not match')


    def test_add_item_blank_dictionary(self):
        item = {}

        self.cur.execute("SELECT COUNT(*) FROM items")  # getting record count before insert
        count1 = self.cur.fetchone()[0]

        error_message = add_items(item, db_file=db_file_test)[0]  # Executing function

        self.cur.execute("SELECT COUNT(*) FROM items")
        count2 = self.cur.fetchone()[0]

        self.assertEqual(count1, count2, 'A record was unexpectedly inserted')
        self.assertEqual(error_message, 'Error adding record to database.', 'Error message did not match')



class TestGetItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):  # Creates the Items table if it doesn't already exist in Test DB, and adds a couple of records
        cls.conn = create_connection(db_file_test)
        cls.conn.row_factory = sqlite3.Row
        cls.cur = cls.conn.cursor()
        cls.cur.execute('''
                CREATE TABLE IF NOT EXISTS items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                item_description TEXT
                );
            ''')

        cls.conn.commit()

        # Inserting 2 records to ensure multiple records can be returned later
        cls.cur.execute("INSERT INTO items (item_name, item_description) VALUES (?,?)",
                        ('Test Item 1', 'Description 1'))
        cls.cur.execute("INSERT INTO items (item_name, item_description) VALUES (?,?)",
                        ('Test Item 2', 'Description 2'))
        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_valid_all_items(self):
        items = get_items(db_file=db_file_test)
        self.assertGreaterEqual(len(items), 2, "Record count was not at least 2.")

    def test_valid_item_id(self):
        items = get_items(db_file=db_file_test)
        valid_item_id = items[0]['item_id']
        item = get_items(valid_item_id, db_file=db_file_test)

        self.assertEqual(len(item), 1, "Length of the return was longer than 1. A single record should be returned.")
        self.assertEqual(item[0], items[0])

    def test_invalid_item_id(self):
        item = get_items(-1, db_file=db_file_test)
        self.assertEqual(item, [], "Records were returned. This test should return an empty list because no id is -1.")


class TestAddInventory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):  # Creates the Items table if it doesn't already exist in Test DB, and adds a couple of records
        cls.conn = create_connection(db_file_test)
        cls.conn.row_factory = sqlite3.Row
        cls.cur = cls.conn.cursor()
        cls.cur.execute('''
                    CREATE TABLE IF NOT EXISTS items (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT NOT NULL,
                    item_description TEXT
                    );
                ''')

        # Inserting a record to ensure inventory can associate to an item
        cls.cur.execute("INSERT INTO items (item_name, item_description) VALUES (?,?)",
                        ('Test Item 1', 'Test Item Description'))

        cls.cur.execute('''
                    CREATE TABLE IF NOT EXISTS inventory (
                    inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    location_string TEXT,
                    FOREIGN KEY (item_id) REFERENCES ITEMS (item_id)
                    );
                ''')
        cls.conn.commit()


    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_add_valid_inventory(self):
        items = get_items(db_file=db_file_test)
        valid_item_id = items[0]['item_id']
        inventory_entry = {'item_id': valid_item_id, 'quantity': 1, 'location_string':'LocationStringExample'}
        error_message = add_inventory(inventory_entry, db_file=db_file_test)

        self.assertEqual(error_message, '', "Empty string was not returned for error message.")

        self.cur.execute("SELECT * FROM INVENTORY WHERE item_id = ? AND quantity = ? AND location_string = ?",
                         (inventory_entry['item_id'], inventory_entry['quantity'], inventory_entry['location_string']))
        result = self.cur.fetchone()
        self.assertIsNotNone(result, "A record matching the inventory entry was not returned.")


    def test_add_inventory_without_item_id(self):
        inventory_entry = {'quantity': 1, 'location_string':'LocationStringExample'}

        self.cur.execute('SELECT COUNT(*) FROM INVENTORY')
        count_before = self.cur.fetchone()[0]

        error_message = add_inventory(inventory_entry, db_file=db_file_test)

        self.cur.execute('SELECT COUNT(*) FROM INVENTORY')
        count_after = self.cur.fetchone()[0]

        self.assertEqual(error_message, 'Error adding record to database.',
                         'Error message did not match did not match expected output')
        self.assertEqual(count_before, count_after, 'Record count unexpectedly changed.')


    def test_add_inventory_empty_dict(self):
        inventory_entry = {}

        self.cur.execute('SELECT COUNT(*) FROM INVENTORY')
        count_before = self.cur.fetchone()[0]

        error_message = add_inventory(inventory_entry, db_file=db_file_test)

        self.cur.execute('SELECT COUNT(*) FROM INVENTORY')
        count_after = self.cur.fetchone()[0]

        self.assertEqual(error_message, 'Error adding record to database.',
                         'Error message did not match did not match expected output')
        self.assertEqual(count_before, count_after, 'Record count unexpectedly changed.')


class TestGetInventory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):  # Creates the Items table if it doesn't already exist in Test DB, and adds a couple of records
        cls.conn = create_connection(db_file_test)
        cls.conn.row_factory = sqlite3.Row
        cls.cur = cls.conn.cursor()

        cls.cur.execute('''
                    CREATE TABLE IF NOT EXISTS items (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT NOT NULL,
                    item_description TEXT
                    );
                ''')

        cls.conn.commit()

        # Inserting a record to ensure inventory can associate to an item
        cls.cur.execute("INSERT INTO items (item_name, item_description) VALUES (?,?)",
                        ('Test Item 1', 'Test Item Description'))

        cls.conn.commit()

        cls.cur.execute('''
                    CREATE TABLE IF NOT EXISTS inventory (
                    inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    location_string TEXT,
                    FOREIGN KEY (item_id) REFERENCES ITEMS (item_id)
                    );
                ''')

        cls.conn.commit()

        items = get_items(db_file=db_file_test)
        valid_item_id = items[0]['item_id']

        # Inserting 2 records to ensure multiple records can be returned later
        cls.cur.execute("INSERT INTO inventory (item_id, quantity, location_string) VALUES (?,?,?)",
                        (valid_item_id, 10, 'Location1'))
        cls.cur.execute("INSERT INTO inventory (item_id, quantity, location_string) VALUES (?,?,?)",
                        (valid_item_id, 5, 'Location2'))
        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()


    def test_valid_all_inventory(self):
        inventory = get_inventory(db_file=db_file_test)
        self.assertGreaterEqual(len(inventory), 2, "Record count was not at least 2.")

    def test_valid_item_id(self):
        inventory = get_inventory(db_file=db_file_test)
        valid_item_id = inventory[0]['inventory_id']
        inventory_entry = get_inventory(valid_item_id, db_file=db_file_test)

        self.assertEqual(len(inventory_entry), 1, "Length of the return was longer than 1. A single record should be returned.")
        self.assertEqual(inventory_entry[0], inventory[0])

    def test_invalid_item_id(self):
        item = get_inventory(-1, db_file=db_file_test)
        self.assertEqual(item, [], "Records were returned. This test should return an empty list because no id is -1.")




if __name__ == '__main__':
    unittest.main()
