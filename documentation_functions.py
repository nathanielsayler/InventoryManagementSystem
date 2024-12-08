
def get_post_list():

    post_list = [
    {
        'author': 'Nathan Sayler',
        'title': 'How to Use this Application',
        'content': '''Instructions for using each link in the sidebar is shared in the links below.''',
        'date_posted': '09/15/24'
    },
    {
        'author': 'Nathan Sayler',
        'title': 'Documentation',
        'content': '''The Documentation link re-directs the user to this page. Each link in the sidebar has a post on this page detailing its functionality.''',
        'date_posted': '11/24/24'
    },
    {
        'author': 'Nathan Sayler',
        'title': 'Configure New Item',
        'content': '''This page allows the user to add items, descriptions, and images to the database. These items are referenced by the listing and inventory functions for faster data entry.
        
        This page has a field for item name and item description, and a button to upload photo from file.''',
        'date_posted': '11/24/24'
    },
    {
        'author': 'Nathan Sayler',
        'title': 'Manage Items',
        'content': '''This page allows the user to view all items that have been configured in the database. By clicking the links in the view/modify column, the user can edit existing items to change photos, item names, descriptions, or delete the entry altogether.''',
        'date_posted': '11/24/24'
    },
    {
        'author': 'Nathan Sayler',
        'title': 'Add Inventory',
        'content': '''This page allows the user to add inventory associated with items that have been configured.
        
        Each inventory entry contains an item from the items page, quantity of the item, location that the item is stored, and Unit Cost Per Item. 
        
        The intent of this page is to associate with a physical tracking system to allow the user to keep track of all their inventory. 
        
        Inventory is also used as a basis for item cost for reporting. When new inventory is added, items are "netted". This means that when a new inventory entry is added, if the Item/Locator String combination already exists in the database, the items are added to the existing entry, and the unit costs are weighted averaged based on count for each entry.''',
        'date_posted': '11/24/24'
    },
    {
        'author': 'Nathan Sayler',
        'title': 'Manage Inventory',
        'content': '''This page allows the user to view and modify inventory entries. By clicking the links in the view/modify column, individual inventory entries can be edited or deleted on the page that follows.''',
        'date_posted': '11/24/24'
    },
    {
        'author': 'Nathan Sayler',
        'title': 'Create Listing',
        'content': '''This page allows the user to record listings made on various online sales platforms like Amazon, Etsy, and Ebay.
        
        This page allows the user to track Item, Quantity, Listing Website, URL of the listing, price per item of the listing, and listing status.''',
        'date_posted': '11/24/24'
    },
    {
        'author': 'Nathan Sayler',
        'title': 'Manage Listings',
        'content': '''This page allows the user to view, modify, and delete all listings recorded in the database.
        
        The user can also record a sale which decrements the quantity on the listing, and records a sale transaction in the database which is used for profitability and inventory reproting.''',
        'date_posted': '11/24/24'
    },
    {
        'author': 'Nathan Sayler',
        'title': 'Ship Item',
        'content': '''This page allows the user to enter shipping sender and recipient details and view FedEx shipping prices and expected delivery dates for an array of shipping options.
        
        In the table of shipping options shared in the table, the user can select an option to get a .pdf file with the shipping label generated.''',
        'date_posted': '11/24/24'
    },
    {
        'author': 'Nathan Sayler',
        'title': 'Profit Report',
        'content': '''This page allows the user to view a report of Monthly Profit and Monthly Margin for a specified item.
        
        To use the report, navigate to the page, select an item from the dropdown menu an press Run Report. Note: This report requires transaction data to provide useful results. For demo purposes, it is suggested to use the SARIMA_Demo_Item entry in the dropdown to display expected results.''',
        'date_posted': '11/24/24'
    },
    {
        'author': 'Nathan Sayler',
        'title': 'Inventory Report',
        'content': '''This page allows the user to view a report of Monthly Inventory quantities for a specified item.
        
        To use the report, navigate to the page, select an item from the dropdown menu an press Run Report. Note: This report requires transaction data to provide useful results. For demo purposes, it is suggested to use the Inventory History Item entry in the dropdown to display expected results.''',
        'date_posted': '11/24/24'
    },
    {
        'author': 'Nathan Sayler',
        'title': 'Sales Forecast',
        'content': '''This page allows the user to view historic sales for a specified item, and projected future sales for the item using a SARIMA (Seasonal Autoregressive Integrated Moving Average) model.
        
        To use the report, navigate to the page, select an item from the dropdown menu an press Run Report. Note: This report requires transaction data to provide useful results. For demo purposes, suggest using the SARIMA_Demo_Item entry in the dropdown to display expected results.
        
        This report does require significant calculation time to generate projected future sales. Please allow up to 30 seconds for this report to run.''',
        'date_posted': '11/24/24'
    }
]

    return post_list