"""
I use API code from Campaign Monitor (https://www.campaignmonitor.com/api/v3-3/getting-started/).

INPUT:
  1. Daily e-report from BusinessQ Analytics.
OUTPUT:
  1. Customers are uploaded to Campaign Monitor ("Clover Orders" list).

Basically, all customers who entered their email (except those, who purchased smth online) will be uploaded to Campaign Monitor.
"""

from createsend import Subscriber
import pandas as pd
from google.colab import files

# Replace with your API key and list ID
API_KEY = "###"
LIST_ID = "###"
CUSTOM_FIELD_KEY = "[ZipCode]"  # Ensure this is the correct key from API

# Initialize the Subscriber object with API key authentication
subscriber_obj = Subscriber({'api_key': API_KEY})

# let users upload excel with customer info
uploaded = files.upload()
uploaded_files = list(uploaded.keys())
print("Uploaded files:", uploaded_files)
print()

# select the file and change it
sales_data = pd.read_excel(uploaded_files[0])
sales_data = sales_data.iloc[24:1000, :5]

# drop values that are N/A for name
sales_data = sales_data.dropna(subset=['CUSTOMER EMAIL'])

# drop items that were purchased online
sales_data = sales_data[sales_data['MERCHANT NAME'] != 'Online']

# assign name, email, zip code values to list
subscribers_list = []

for _, row in sales_data.iterrows():
    customer_name = row["CUSTOMER NAME"]

    # If "CUSTOMER NAME" is "N/A" or NaN, replace it with an empty string
    if pd.isna(customer_name) or customer_name == "N/A":
        customer_name = ""

    placeholder_dict = {
        "EmailAddress": str(row["CUSTOMER EMAIL"]),  # Ensure email is a string
        "Name": customer_name,  # Use the corrected name value
        "CustomFields": [
            {"Key": "ZipCode",
             "Value": str(row["CUSTOMER ZIP CODE"])} # change to text
        ],
        "ConsentToTrack": "Yes"
    }

    subscribers_list.append(placeholder_dict)

try:
    # Import multiple subscribers into the list
    response = subscriber_obj.import_subscribers(
        list_id=LIST_ID,
        subscribers=subscribers_list,  # Pass only the list, not a dictionary
        resubscribe=True,  # Allow resubscribing inactive users
        queue_subscription_based_autoresponders=True,  # Trigger autoresponders
        restart_subscription_based_autoresponders=True  # Restart autoresponder sequences for resubscribed users
    )
    print("Subscribers imported successfully!", response)
except Exception as e:
    print(f"Error importing subscribers: {e}")
