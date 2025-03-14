from fileinput import filename
from os.path import basename

from numpy.ma.testutils import assert_equal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import pandas as pd
import glob
import unittest
import hashlib
import requests
from inventoryDbFunctions import get_listings, get_items
from bs4 import BeautifulSoup

from inventoryUnitTests import Default_Directory
download_location = Default_Directory+"\\selenium_downloads"

# Initialize WebDriver (replace with the path to your ChromeDriver if needed)
edgeOptions = webdriver.EdgeOptions()
prefs = {"download.default_directory": download_location, 'profile.default_content_setting_values.automatic_downloads': 1}
edgeOptions.add_experimental_option("prefs", prefs)

def get_md5_checksum(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def clear_downloads():
    # Deletes any files that may already be present in Selenium downloads folder
    for f in os.listdir(download_location):
        os.remove(os.path.join(download_location, f))


class Test_ST5(unittest.TestCase):

    def test_csv_download_verify_st5(self):
        clear_downloads()
        try:
            #Opening the webpage
            driver = webdriver.Edge(options=edgeOptions)
            driver.get("http://192.168.86.23:3839/")  # Navigate to the Web App
            time.sleep(1)

            # Clicking the Manage Inventory link
            manage_inventory_xpath = '/html/body/main/div/div[1]/div[1]/ul/li/a[5]'
            manage_inventory_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, manage_inventory_xpath)))
            manage_inventory_link.click()
            time.sleep(1)

            # Clicking the download to CSV button
            download_csv_xpath = '/html/body/main/div/div[2]/div/a'
            download_csv_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, download_csv_xpath)))

            download_csv_link.click()
            time.sleep(5)

            # Getting results into a DataFrame. Code below supports multiple download files, though unnecessary in this case
            filenames = glob.glob(download_location + "\*.csv")

            # Verifying exactly 1 file was downloaded
            self.assertEqual(len(filenames), 1, "Exactly 1 file should be downloaded")

            # Verifying contents of file contain at least the expected columns
            df_result = pd.DataFrame()
            for file in filenames:
                df = pd.read_csv(file)
                df_result = pd.concat([df_result, df])

            column_list = df_result.columns.tolist()
            expected_columns = ['inventory_id', 'item_id', 'item_name', 'quantity', 'location_string']
            self.assertTrue(set(expected_columns).issubset(column_list), 'Some columns are missing.')

            # Verifying the format of the filename
            regex_filename = r"^inventory_download_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.csv$"
            actual_filename = os.path.basename(filenames[0])
            self.assertRegex(actual_filename, regex_filename, "File name format is not correct.")

        finally:
            # Close the browser
            driver.quit()


class Test_ST6(unittest.TestCase):

    def test_image_upload(self):
        clear_downloads()
        try:
            #Opening the webpage
            driver = webdriver.Edge(options=edgeOptions)
            driver.get("http://192.168.86.23:3839/")  # Navigate to the Web App
            time.sleep(1)

            # Clicking the Configure New Item link
            manage_items_xpath = '/html/body/main/div/div[1]/div[1]/ul/li/a[2]'
            manage_items_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, manage_items_xpath)))
            manage_items_link.click()
            time.sleep(1)

            # Filling out form fields
            item_name = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="item_name"]')))
            item_name.send_keys('ST6 Verification Item')

            item_description = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="item_description"]')))
            item_description.send_keys('ST6 Verification Item Description')

            image_file_path = Default_Directory + "\\selenium_assets\\dolphintest.png"
            upload_file_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="item_photo"]')))
            upload_file_button.send_keys(image_file_path)

            save_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="submit"]')))
            time.sleep(1)
            save_button.click()

            #Should re-direct to table of results page. We will find our result in the html table by iterating
            html_table = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/main/div/div[2]/table')))
            rows = html_table.find_elements(By.XPATH, './/tr')
            for row in rows:
                if 'ST6 Verification Item' in row.text:
                    link = row.find_element(By.XPATH, ".//a")
                    link.click()
                    break
            time.sleep(1)

            # Should re-direct to the record we previously created. Now we'll download the image to compare MD5 Checksum
            test_image = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/main/div/div[2]/div/form/fieldset/div/div/img')))

            # Downloading the image
            image_link = test_image.get_attribute("src")
            response = requests.get(image_link)
            image_name = os.path.basename(image_link)
            save_path = os.path.join(download_location, image_name)
            with open(save_path, "wb") as f:
                f.write(response.content)

            md5_downloaded_image = get_md5_checksum(save_path)
            md5_uploaded_image = get_md5_checksum(image_file_path)

            # Verifying exactly 1 file was downloaded
            self.assertEqual(md5_uploaded_image, md5_downloaded_image)

            # Deleting image and record to keep db clean
            image_delete_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/main/div/div[2]/div/form/fieldset/div/div/button')))
            image_delete_button.click()
            time.sleep(1)

            record_delete_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="delete_button"]')))
            record_delete_button.click()
            time.sleep(1)

        finally:
            # Close the browser
            driver.quit()


class Test_ST7(unittest.TestCase):

    def test_listings_functionality(self):
        clear_downloads()
        try:
            #Opening the webpage
            driver = webdriver.Edge(options=edgeOptions)
            driver.get("http://192.168.86.23:3839/")  # Navigate to the Web App
            time.sleep(1)

            # Clicking the Configure New Item link
            configure_item_xpath = '/html/body/main/div/div[1]/div[1]/ul/li/a[2]'
            configure_item_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, configure_item_xpath)))
            configure_item_link.click()
            time.sleep(1)

            # Filling out form fields
            item_name = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="item_name"]')))
            item_name.send_keys('ST7 Verification Item')

            item_description = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="item_description"]')))
            item_description.send_keys('ST7 Verification Item Description')

            save_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="submit"]')))
            time.sleep(1)
            save_button.click()

            # Clicking the Create Listing Link
            create_listing_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/main/div/div[1]/div[1]/ul/li/a[6]')))
            create_listing_link.click()

            item_name = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="item_id"]')))
            item_name.send_keys('ST7 Verification Item')

            item_quantity = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="quantity"]')))
            item_quantity.send_keys('5')

            website = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="website"]')))
            website.send_keys('Amazon')

            listing_price = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="unit_price"]')))
            listing_price.send_keys('10.50')

            url = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="listing_url"]')))
            url.send_keys('About:Blank')

            listing_status = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="listing_status"]')))
            listing_status.send_keys('active')

            save_button2 = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="submit"]')))
            save_button2.click()
            time.sleep(3)

            #Performing verification of data
            items = get_items()
            listings = get_listings()

            items_df = pd.DataFrame(items)
            listings_df = pd.DataFrame(listings)

            merged_df = pd.merge(listings_df, items_df, how='left', on='item_id')
            merged_df.to_csv('test.csv')

            filtered_df = merged_df[merged_df['item_name'] == 'ST7 Verification Item']

            dictionary_output = filtered_df.to_dict(orient='records')
            listing_record = dictionary_output[0]

            # Verifying all input values
            self.assertEqual(listing_record['item_name'], 'ST7 Verification Item')
            self.assertEqual(listing_record['quantity'], 5)
            self.assertEqual(listing_record['website'], 'Amazon')
            self.assertEqual(listing_record['listing_url'], 'About:Blank')
            self.assertEqual(listing_record['listing_status'], 'active')


            #cleanup
            #Should re-direct to table of results page. We will find and delete our new record to clean up
            html_table = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/main/div/div[2]/table')))
            rows = html_table.find_elements(By.XPATH, './/tr')
            for row in rows:
                if 'ST7 Verification Item' in row.text:
                    link = row.find_element(By.XPATH, ".//a")
                    link.click()
                    break
            time.sleep(1)

            #Deleting the record
            record_delete_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="delete_button"]')))
            record_delete_button.click()
            time.sleep(1)

            #Navigating to all items to delete that record as well
            manage_items_xpath = '/html/body/main/div/div[1]/div[1]/ul/li/a[3]'
            manage_items_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, manage_items_xpath)))
            manage_items_link.click()
            time.sleep(1)

            html_table = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/main/div/div[2]/table')))
            rows = html_table.find_elements(By.XPATH, './/tr')
            for row in rows:
                if 'ST7 Verification Item' in row.text:
                    link = row.find_element(By.XPATH, ".//a")
                    link.click()
                    break
            time.sleep(1)

            #Deleting the record
            record_delete_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="delete_button"]')))
            record_delete_button.click()
            time.sleep(3)

            deleted_listing = get_listings(listing_record['listing_id'])
            deleted_item = get_items(listing_record['item_id'])

            # Verifying that we get an empty list when querying the id's of the records we just deleted
            self.assertEqual(len(deleted_item), 0)
            self.assertEqual(len(deleted_listing), 0)


        finally:
            # Close the browser
            driver.quit()


class Test_ST8(unittest.TestCase):

    def test_profit_report_st8(self):
        try:
            #Opening the webpage
            driver = webdriver.Edge(options=edgeOptions)
            driver.get("http://192.168.86.23:3839/")  # Navigate to the Web App
            time.sleep(1)

            # Clicking the Profit Report link
            profit_report_xpath = '/html/body/main/div/div[1]/div[2]/ul/li/a[1]'
            profit_report_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, profit_report_xpath)))
            profit_report_link.click()
            time.sleep(1)

            # Setting the Item dropdown to SARIMA_Demo_Item
            item_dropdown_xpath = '//*[@id="item_id"]'
            item_dropdown = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, item_dropdown_xpath)))
            item_dropdown.send_keys('SARIMA_Demo_Item')

            # Pressing the submit button
            submit_button_xpath = '//*[@id="submit"]'
            submit_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, submit_button_xpath)))
            submit_button.click()

            #Verifying chart titles
            title_elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.gtitle')))
            self.assertEqual(title_elements[0].text, "Monthly Profit")
            self.assertEqual(title_elements[1].text, "Monthly Margin")

            #Verifying y-axis titles
            yaxis_titles = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.ytitle')))
            self.assertEqual(yaxis_titles[0].text, "Profit ($)")
            self.assertEqual(yaxis_titles[1].text, "Margin (%)")

            #Verifying x-axis titles
            xaxis_titles = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.xtitle')))
            self.assertEqual(xaxis_titles[0].text, "Month")
            self.assertEqual(xaxis_titles[1].text, "Month")

            time.sleep(1)


        finally:
            # Close the browser
            driver.quit()


class Test_ST9(unittest.TestCase):

    def test_inventory_report_st9(self):
        try:
            #Opening the webpage
            driver = webdriver.Edge(options=edgeOptions)
            driver.get("http://192.168.86.23:3839/")  # Navigate to the Web App
            time.sleep(1)

            # Clicking the Inventory Report link
            inventory_report_xpath = '/html/body/main/div/div[1]/div[2]/ul/li/a[2]'
            inventory_report_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, inventory_report_xpath)))
            inventory_report_link.click()
            time.sleep(1)

            # Setting the Item dropdown to Inventory History Item
            item_dropdown_xpath = '//*[@id="item_id"]'
            item_dropdown = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, item_dropdown_xpath)))
            item_dropdown.send_keys('Inventory History Item')

            # Pressing the submit button
            submit_button_xpath = '//*[@id="submit"]'
            submit_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, submit_button_xpath)))
            submit_button.click()

            title_elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.gtitle')))
            self.assertEqual(title_elements[0].text, "Monthly Inventory Levels")

            yaxis_titles = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.ytitle')))
            self.assertEqual(yaxis_titles[0].text, "Inventory Level")

            xaxis_titles = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.xtitle')))
            self.assertEqual(xaxis_titles[0].text, "Month")

            time.sleep(1)


        finally:
            # Close the browser
            driver.quit()


class Test_ST10(unittest.TestCase):

    def test_sales_prediction_st10(self):
        try:
            #Opening the webpage
            driver = webdriver.Edge(options=edgeOptions)
            driver.get("http://192.168.86.23:3839/")  # Navigate to the Web App
            time.sleep(1)

            # Clicking the Sales Forecast link
            profit_report_xpath = '/html/body/main/div/div[1]/div[2]/ul/li/a[3]'
            profit_report_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, profit_report_xpath)))
            profit_report_link.click()
            time.sleep(1)

            # Setting the Item dropdown to SARIMA_Demo_Item
            item_dropdown_xpath = '//*[@id="item_id"]'
            item_dropdown = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, item_dropdown_xpath)))
            item_dropdown.send_keys('SARIMA_Demo_Item')

            # Pressing the submit button
            submit_button_xpath = '//*[@id="submit"]'
            submit_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, submit_button_xpath)))
            submit_button.click()

            WebDriverWait(driver, 120).until(EC.url_contains("sales_forecast"))
            time.sleep(5)

            #Verifying title
            title_elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.gtitle')))
            self.assertEqual(title_elements[0].text, "Sales Forecast using SARIMA Model with Yearly Seasonality")

            #Verifying y-axis title
            yaxis_titles = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.ytitle')))
            self.assertEqual(yaxis_titles[0].text, "Quantity Sold")

            #Verifying x-axis title
            xaxis_titles = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.xtitle')))
            self.assertEqual(xaxis_titles[0].text, "Date")

            #Verifying legend text
            legend_text = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.legendtext')))
            self.assertEqual(legend_text[0].text, "Observed")
            self.assertEqual(legend_text[1].text, "Forecast")

            time.sleep(1)


        finally:
            # Close the browser
            driver.quit()


class Test_ST11(unittest.TestCase):

    def test_documentation_page_st11(self):
        try:

            # Opening the webpage
            driver = webdriver.Edge(options=edgeOptions)
            driver.get("http://192.168.86.23:3839/")  # Navigate to the Web App
            time.sleep(1)


            # Finding all sidebar links
            sidebar_links = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".bd-sidebar a.list-group-item-light"))
            )

            # Extracting names of links in the sidebar
            link_text_entries = []
            for link in sidebar_links:
                text = link.text.strip()
                if text:  # Make sure we have non-empty text
                    link_text_entries.append(text)

            print(link_text_entries)

            # Getting titles of posts on the page
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.media")))

            # 4. Extract titles from the documentation posts
            # The titles are inside: <h2><a class="article-title" href="#">{{ post.title }}</a></h2>
            doc_titles_elements = driver.find_elements(By.CSS_SELECTOR, "h2 a.article-title")
            doc_titles = [title_el.text.strip() for title_el in doc_titles_elements]

            print(doc_titles)

            # 5. Verify that every sidebar link is documented
            missing_docs = [text for text in link_text_entries if text not in doc_titles]

            assert_equal(missing_docs, [])

            if missing_docs:
                raise AssertionError(f"Missing documentation for these links: {missing_docs}")
            else:
                print("All sidebar links have corresponding documentation posts.")

            time.sleep(1)

        finally:
            driver.quit()


class Test_ST12(unittest.TestCase):

    def test_ship_item_rates_st12(self):
        try:

            # Opening the webpage
            driver = webdriver.Edge(options=edgeOptions)
            driver.get("http://192.168.86.23:3839/")  # Navigate to the Web App
            time.sleep(1)

            # Clicking the Ship Item link
            profit_report_xpath = '/html/body/main/div/div[1]/div[1]/ul/li/a[8]'
            profit_report_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, profit_report_xpath)))
            profit_report_link.click()
            time.sleep(1)

            # Filling out all fields in the form
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sender_zip_code"]'))).send_keys('78723')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sender_city"]'))).send_keys('Austin')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sender_state"]'))).send_keys('TX')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sender_street_address"]'))).send_keys('123 Example Street')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sender_name"]'))).send_keys('John Doe')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sender_phone"]'))).send_keys('1234567890')

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="recipient_zip_code"]'))).send_keys('90210')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="recipient_city"]'))).send_keys('Los Angeles')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="recipient_state"]'))).send_keys('CA')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="recipient_street_address"]'))).send_keys('321 Example Street')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="recipient_name"]'))).send_keys('Jane Smith')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="recipient_phone"]'))).send_keys('09876654321')

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="item_weight"]'))).send_keys('3')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="package_length"]'))).send_keys('4')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="package_width"]'))).send_keys('5')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="package_height"]'))).send_keys('6')

            submit_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="submit"]')))
            submit_button.click()

            time.sleep(1)

            # Wait up to 10 seconds for the table to appear
            table_headers = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//table//th')))

            header_texts = [header.text.strip() for header in table_headers]

            # Asserting that each of the expected columns is present in the table that is generated
            expected_columns = ["Service Name", "Total Cost (USD)", "Estimated Delivery"]
            for column in expected_columns:
                # Using unittest style assertion
                print(column, header_texts)
                self.assertIn(column, header_texts, f"Column '{column}' not found in table headers {header_texts}")

            time.sleep(1)

        finally:
            driver.quit()


class Test_ST13(unittest.TestCase):

    def test_ship_item_label_st13(self):
        try:
            clear_downloads()
            # Opening the webpage
            driver = webdriver.Edge(options=edgeOptions)
            driver.get("http://192.168.86.23:3839/")  # Navigate to the Web App
            time.sleep(1)

            # Clicking the Ship Item link
            profit_report_xpath = '/html/body/main/div/div[1]/div[1]/ul/li/a[8]'
            profit_report_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, profit_report_xpath)))
            profit_report_link.click()
            time.sleep(1)

            # Filling out all fields in the form
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sender_zip_code"]'))).send_keys('78723')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sender_city"]'))).send_keys('Austin')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sender_state"]'))).send_keys('TX')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sender_street_address"]'))).send_keys('123 Example Street')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sender_name"]'))).send_keys('John Doe')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sender_phone"]'))).send_keys('1234567890')

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="recipient_zip_code"]'))).send_keys('90210')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="recipient_city"]'))).send_keys('Los Angeles')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="recipient_state"]'))).send_keys('CA')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="recipient_street_address"]'))).send_keys('321 Example Street')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="recipient_name"]'))).send_keys('Jane Smith')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="recipient_phone"]'))).send_keys('0987654321')

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="item_weight"]'))).send_keys('3')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="package_length"]'))).send_keys('4')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="package_width"]'))).send_keys('5')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="package_height"]'))).send_keys('6')

            submit_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="submit"]')))
            submit_button.click()

            time.sleep(3)

            # Wait up to 10 seconds for the table to appear, then clicking the first link
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/main/div/div[2]/div/div/table/tbody/tr[1]/td[6]/form/button'))).click()

            time.sleep(10)  # Allow file to download before closing window

            # Getting results into a DataFrame. Code below supports multiple download files, though unnecessary in this case
            filenames = glob.glob(download_location + "\*.pdf")
            actual_filename = os.path.basename(filenames[0])

            # Verifying exactly 1 file was downloaded
            self.assertEqual(len(filenames), 1, "Exactly 1 file should be downloaded")

            # Verifying that the filename is in expected format
            self.assertEqual(actual_filename, 'shipping_label.pdf')

        finally:
            driver.quit()

if __name__ == "__main__":
    unittest.main(verbosity=2)