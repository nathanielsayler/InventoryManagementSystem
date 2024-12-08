import sqlite3
import unittest
import pathlib
from inventoryWebApp import app
from unittest.mock import patch, MagicMock
from io import BytesIO
import pandas as pd
from flask import url_for
import os
from bs4 import BeautifulSoup
import json


from inventoryDbFunctions import create_connection, add_items, get_items, add_inventory, get_inventory, get_listings
from sarimaModelPredict import generate_profit_report, generate_inventory_history, create_forecast_plot_html
from documentation_functions import get_post_list
from FedExAPI import get_access_token, get_rates_and_transit_times, parse_rate_response, generate_shipping_label

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
                    unit_price REAL,
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
        inventory_entry = {'item_id': valid_item_id, 'quantity': 1, 'location_string': 'LocationStringExample', 'unit_price': 10.25}
        error_message = add_inventory(inventory_entry, db_file=db_file_test)

        self.assertEqual(error_message, '', "Empty string was not returned for error message.")

        self.cur.execute("SELECT * FROM INVENTORY WHERE item_id = ? AND quantity = ? AND location_string = ? AND unit_price = ?",
                         (inventory_entry['item_id'], inventory_entry['quantity'], inventory_entry['location_string'], inventory_entry['unit_price']))
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


# Testing generation of Profit Report
class TestProfitReport(unittest.TestCase):

    def test_generate_profit_report(self):
        #Create mocked data to simulate input
        synthetic_data = [
            {'date_sold': '01-15-2023', 'quantity': 10, 'sale_price': 20, 'acquisition_cost': 15},
            {'date_sold': '02-15-2023', 'quantity': 5, 'sale_price': 25, 'acquisition_cost': 10},
            {'date_sold': '03-15-2023', 'quantity': 20, 'sale_price': 30, 'acquisition_cost': 20}
        ]

        #Call the generate_profit_report function with mocked data
        report_html = generate_profit_report(synthetic_data)

        #Verify chart labels in the HTML output
        self.assertIn('"title":{"text":"Monthly Profit"}', report_html, "Missing 'Monthly Profit' title.")
        self.assertIn('"title":{"text":"Monthly Margin"}', report_html, "Missing 'Monthly Margin' title.")


        self.assertIn('"y":[50,75,200],"type":"bar"', report_html, "Missing profit value(s).")
        self.assertIn('"y":[25.0,60.0,33.33333333333333],"type":"scatter"', report_html, "Missing margin value(s).")


class TestInventoryHistoryReport(unittest.TestCase):

    def test_generate_inventory_history(self):
        #Create synthetic data to simulate input
        current_inventory = [
            {'quantity': 123456543},
        ]
        inventory_history = [
            {'date': '2023-01-15', 'qty_change': 10},
            {'date': '2023-02-15', 'qty_change': -5},
            {'date': '2023-03-15', 'qty_change': 20},
        ]

        #Call the generate_inventory_history function with synthetic data
        report_html = generate_inventory_history(current_inventory, inventory_history)

        #Verify chart labels in the HTML output
        self.assertIn('"title":{"text":"Monthly Inventory Levels"}', report_html,
                      "Missing 'Monthly Inventory Levels' title.")
        self.assertIn('"yaxis":{"title":{"text":"Inventory Level"}}', report_html, "Missing 'Inventory Level' title.")

        #Check that expected inventory levels appear in the HTML
        self.assertIn('"y":[123456523,123456528,123456518],"type":"bar"}],', report_html,"Inventory values did not match expected output")


class TestInventoryForecastReport(unittest.TestCase):

    def test_create_forecast_plot_html(self):
        #Load synthetic data from CSV file
        data_input_df = pd.read_csv("SARIMA_Demo_Item.csv")
        data_input_df['quantity'] = data_input_df['qty_sold']
        data_input_df['date_sold'] = pd.to_datetime(data_input_df['date_sold'], format='%m/%d/%Y').dt.strftime('%m-%d-%Y')

        data_input = data_input_df.to_dict(orient="records")

        #Call the create_forecast_plot_html function with the data from CSV
        report_html = create_forecast_plot_html(data_input)
        with open("report_html_output.txt", "w", encoding="utf-8") as file:
            file.write(repr(report_html))

        #Verify chart labels in the HTML output
        self.assertIn('"title":{"text":"Sales Forecast using SARIMA Model with Yearly Seasonality"}', report_html,
                      "Matching title not found in generated report.")
        self.assertIn('"yaxis":{"title":{"text":"Quantity Sold"}}', report_html, "Matching y-axis title 'Quantity Sold' not found in generated report.")

        #Verify the presence of future dates in the forecast
        #Use the expected last date in the historical data and confirm forecast dates extend beyond it
        historical_data = pd.DataFrame(data_input)
        historical_data['Date'] = pd.to_datetime(historical_data['date_sold'], format='%m-%d-%Y')
        last_date = historical_data['Date'].max()

        #Check the next 12 months to look for future date
        future_date_found = False
        for i in range(1, 13):
            future_date = (last_date + pd.DateOffset(months=i)).strftime('%Y-%m')
            if future_date in report_html:
                future_date_found = True
                break

        self.assertTrue(future_date_found, "Future dates not found in the chart.")


class TestSidebarLinks(unittest.TestCase):

    def test_sidebar_links_match_posts(self):
        # Parse the HTML file to extract sidebar links
        with open("templates/layout.html", "r", encoding="utf-8") as f:  # Replace with the actual file path
            html_content = f.read()

        # Parsing the HTML using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Extracting Quick Links and Reports links
        quick_links = [
            link.get_text(strip=True) for link in soup.select("div.bd-sidebar .content-section:nth-of-type(1) a")
        ]
        reports_links = [
            link.get_text(strip=True) for link in soup.select("div.bd-sidebar .content-section:nth-of-type(2) a")
        ]

        # Combining all sidebar links into one list
        sidebar_links = quick_links + reports_links

        # Getting the post titles from get_post_list
        post_titles = [post["title"] for post in get_post_list()]

        # Verify that every sidebar link is covered in get_post_list
        for link in sidebar_links:
            self.assertIn(link, post_titles, f"Sidebar link '{link}' is missing from documentation posts.")


class TestGetShippingRates(unittest.TestCase):

    def test_get_shipping_rates(self):

        raw_rates = get_rates_and_transit_times(
            access_token=get_access_token(),
            sender_zip_code="78723",
            recipient_zip_code="90210",
            package_weight="1",
            package_length="2",
            package_width="3",
            package_height="4"
        )

        parsed_rates = parse_rate_response(raw_rates)
        print(parsed_rates)

        self.assertTrue(len(parsed_rates) > 0)

        required_fields = {'ServiceType', 'EstimatedDelivery', 'TotalNetCharge'}
        for entry in parsed_rates:
            self.assertTrue(required_fields.issubset(entry.keys()), f"Missing required fields in entry: {entry}")


class TestGenerateShippingLabel(unittest.TestCase):

    def test_generate_shipping_label(self):

        selected_option = {
            "ServiceType": "FIRST_OVERNIGHT",
            "ServiceName": "FedEx First Overnight",
            "TotalNetCharge": 156.6,
            "SaturdayDelivery": True,
            "EstimatedDelivery": '2024-12-07 11:00 AM'
        }

        fed_ex_access_token = get_access_token()

        shipper = {
            "address": {
                "postalCode": "78723",
                "countryCode": "US",
                "stateOrProvinceCode": "TX",
                "city": "Austin",
                "streetLines": ["123 Example Street"],
                "residential": False
            },
            "contact": {
                "personName": "John Doe",
                "phoneNumber": "1234567890"
            }
        }

        recipient = {
            "address": {
                "postalCode": "90210",
                "countryCode": "US",
                "stateOrProvinceCode": "CA",
                "city": "Los Angeles",
                "streetLines": ["321 Example Street"],
                "residential": True
            },
            "contact": {
                "personName": "Jane Smith",
                "phoneNumber": "0987654321"
            }
        }

        package_details = {
            "weight": {
                "units": "LB",
                "value": "1"
            },
            "dimensions": {
                "length": "2",
                "width": "3",
                "height": "4",
                "units": "IN"
            }
        }

        label_file_path = "shipping_label.pdf"

        response = generate_shipping_label(
            access_token=fed_ex_access_token,
            selected_option=selected_option,
            shipper=shipper,
            recipient=recipient,
            package_details=package_details,
            label_file_path=label_file_path
        )

        # Assert that valid response was received from the label API
        self.assertEqual(response.status_code, 200)

        ship_response = response.json()

        transaction_shipment = ship_response['output']['transactionShipments'][0]
        service_type = transaction_shipment['serviceType']
        package_documents = transaction_shipment['pieceResponses'][0]['packageDocuments'][0]

        self.assertEqual(service_type, "FIRST_OVERNIGHT", "ServiceType did not match expected 'FIRST_OVERNIGHT'")

        self.assertIn("encodedLabel", package_documents, "Did not find encodedLabel key in the packageDocuments")



if __name__ == '__main__':
    unittest.main()
