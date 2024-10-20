import sqlite3
import unittest
import pathlib
from inventoryWebApp import app
from unittest.mock import patch, MagicMock
from io import BytesIO
from flask import url_for
import os


from inventoryDbFunctions import create_connection, add_items, get_items, add_inventory, get_inventory, get_listings

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


# Testing .csv download feature on the inventory page
class TestDownloadInventoryCSV(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        #Setting up the test client
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def mock_get_inventory_with_data(self):
        #Mock inventory data with one record
        return [{'inventory_id': 1, 'item_id': 101, 'quantity': 10, 'location_string': 'A1'}]

    def mock_get_items_with_data(self):
        #Mock items data with one matching record
        return [{'item_id': 101, 'item_name': 'UT5Item'}]

    def mock_get_inventory_empty(self):
        #Mock empty return for inventory database
        return []

    def mock_get_items_empty(self):
        #Mock empty return for items database
        return []

    def assert_csv_content(self, response, expected_content):
        #This function will be used to interpret the .csv contents
        csv_data = response.data.decode('utf-8')
        self.assertIn(expected_content, csv_data)

    @patch('inventoryWebApp.get_inventory', return_value=[{'inventory_id': 1, 'item_id': 101, 'quantity': 10, 'location_string': 'A1'}])
    @patch('inventoryWebApp.get_items', return_value=[{'item_id': 101, 'item_name': 'Widget'}])
    def test_download_inventory_csv_with_data(self, mock_get_inventory, mock_get_items):
        #Testing with mocked valid contents from inventory and items queries
        response = self.client.get('/download_inventory_csv')

        # Assert response is a valid CSV file
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/csv')

        # Validate filename format
        content_disposition = response.headers['Content-Disposition']
        self.assertIn('attachment; filename=', content_disposition)
        filename = content_disposition.split('filename=')[1]
        regex_filename = r"^inventory_download_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.csv$"
        self.assertRegex(filename, regex_filename, "File name format is not correct.")

        # Validate CSV content
        self.assert_csv_content(response, 'inventory_id,item_id,item_name,quantity,location_string')
        self.assert_csv_content(response, '1,101,Widget,10,A1')

    empty_list = []

    @patch('inventoryWebApp.get_items', return_value=empty_list)
    @patch('inventoryWebApp.get_inventory', return_value=empty_list)
    def test_download_inventory_csv_empty(self, mock_get_inventory, mock_get_items):
        #Testing with mocked blank contents from items and inventory
        response = self.client.get('/download_inventory_csv')

        # Assert response is a valid CSV file
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/csv')

        # Validate filename format
        content_disposition = response.headers['Content-Disposition']
        self.assertIn('attachment; filename=', content_disposition)
        filename = content_disposition.split('filename=')[1]
        regex_filename = r"^inventory_download_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.csv$"
        self.assertRegex(filename, regex_filename, "File name format is not correct.")

        # Validate empty CSV except for headers
        self.assert_csv_content(response, 'inventory_id,item_id,item_name,quantity,location_string')


# Testing image upload feature and some basic error handling
class TestImageUpload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        #Setting app parameters for the test. CSRF must be disabled for this test to work properly
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        app.config['UPLOAD_FOLDER'] = 'test_uploads'  # Use a test directory for uploads
        cls.client = app.test_client()

    def tearDown(self):
        #Cleaning up the files after each test
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER'], topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))

    def mock_add_items(self, item):
        #Mocking response from add_items function
        return None, '1'  # Simulate new item_id = 1

    def test_valid_image_upload_for_new_item(self):
        #Test Case 1: Valid upload of image for a new item (index = 0)
        with patch('inventoryWebApp.add_items', self.mock_add_items):
            data = {
                'item_name': 'Test Item',
                'item_description': 'Test Description',
                'item_photo': (BytesIO(b"test image data"), 'dolphintest.png'),
                'submit': 'Save',  # Simulate pressing the submit button
                'index': '0'  # New item
            }
            response = self.client.post('/new_item?index=0', data=data, content_type='multipart/form-data')

            # Assert redirect after successful upload
            self.assertEqual(response.status_code, 302)

            # Check if the new folder was created and the file is saved
            new_item_folder = os.path.join(app.config['UPLOAD_FOLDER'], '1')
            self.assertTrue(os.path.exists(new_item_folder))
            self.assertIn('dolphintest.png', os.listdir(new_item_folder))

    def test_valid_image_upload_for_existing_item(self):
        #Test Case 2: Valid image upload for an existing item (index = item_id)
        item_id = '2'
        existing_item_folder = os.path.join(app.config['UPLOAD_FOLDER'], item_id)
        os.makedirs(existing_item_folder, exist_ok=True)  # Create folder for the existing item

        data = {
            'item_name': 'Existing Item',
            'item_description': 'Existing Description',
            'item_photo': (BytesIO(b"test image data"), 'dolphintest.png'),
            'submit': 'Save',  # Simulate pressing the submit button
            'index': item_id  # Existing item
        }
        response = self.client.post(f'/new_item?index={item_id}', data=data, content_type='multipart/form-data')

        # Assert redirect after successful upload
        self.assertEqual(response.status_code, 302)  # Expecting a redirect

        # Check if the file is saved in the correct folder
        self.assertIn('dolphintest.png', os.listdir(existing_item_folder))

    def test_invalid_file_type_upload(self):
        #Test Case 3: Invalid file type upload - attempt to upload .txt file
        data = {
            'item_name': 'Test Item',
            'item_description': 'Test Description',
            'item_photo': (BytesIO(b"invalid file data"), 'InvalidTest.txt'),
            'submit': 'Save',  # Simulate pressing the submit button
            'index': '0'  # New item
        }
        response = self.client.post('/new_item?index=0', data=data, content_type='multipart/form-data')

        # Assert app does not re-direct after invalid file type uploaded
        self.assertEqual(response.status_code, 200)

        # Assert no new folder was created for the invalid upload
        new_item_folder = os.path.join(app.config['UPLOAD_FOLDER'], '1')
        self.assertFalse(os.path.exists(new_item_folder))


# Testing listings query function
class TestGetListings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):  # Creates the Items table if it doesn't already exist in Test DB, and adds a couple of records
        cls.conn = create_connection(db_file_test)
        cls.conn.row_factory = sqlite3.Row
        cls.cur = cls.conn.cursor()

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
                    CREATE TABLE IF NOT EXISTS listings (
                    listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER,
                    website TEXT,
                    listing_url TEXT,
                    listing_status INTEGER,
                    quantity INTEGER);
                    ''')

        cls.conn.commit()

        items = get_items(db_file=db_file_test)
        valid_item_id = items[0]['item_id']

        # Inserting 2 records to ensure multiple records can be returned later
        cls.cur.execute("INSERT INTO listings (item_id, website, listing_url, listing_status, quantity) VALUES (?,?,?,?,?)",
                        (valid_item_id, 'test website1', 'test_url1', 'Active', 10))
        cls.cur.execute("INSERT INTO listings (item_id, website, listing_url, listing_status, quantity) VALUES (?,?,?,?,?)",
                        (valid_item_id, 'test website2', 'test_url2', 'Active', 10))
        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_valid_all_listings(self):
        # Testing case with valid blank query to return all records
        listings = get_listings(db_file=db_file_test)
        self.assertGreaterEqual(len(listings), 2, "Record count was not at least 2.")

    def test_valid_listing_id(self):
        # Testing case with valid query that calls out a specific listing_id
        listings = get_listings(db_file=db_file_test)
        valid_listing_id = listings[0]['listing_id']
        listing = get_listings(valid_listing_id, db_file=db_file_test)

        self.assertEqual(len(listing), 1, "Length of the return was longer than 1. A single record should be returned.")
        self.assertEqual(listings[0], listing[0])

    def test_invalid_listing_id(self):
        # Testing case with query that should return 0 records
        listing = get_listings(-1, db_file=db_file_test)
        self.assertEqual(listing, [], "Records were returned. This test should return an empty list because no id is -1.")

if __name__ == '__main__':
    unittest.main()
