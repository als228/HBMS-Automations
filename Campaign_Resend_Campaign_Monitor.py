"""
I use API code from Campaign Monitor (https://www.campaignmonitor.com/api/v3-3/getting-started/).

INPUT:
  1. Name of the campaign to resend.
OUTPUT:
  1. Segments are created in lists, affiliated with the entered campaign.

Basically, once we get the name of the campaign to resend, the algorithm goes through all campaigns, finds the one we need.
Then, we go through all lists in that campaign, and create a segment for subscribers who didn't open the 1st email.

NOTE: It is impossible to continue this algorithm further into automatic resend, because the HBMS templates are unique,
      so they don't have TemplateID that you need to create a campaign. Thus, we can only create segments of subscribers
      who didn't open the 1st campaign, then manually create a campaign, select these segments, and resend the campaign.
"""

from createsend import CreateSend, Campaign, List, Segment, Client
import requests
import json
from requests.auth import HTTPBasicAuth

# User inputs
API_KEY = "###"
CLIENT_ID = "###"
campaign_name_input = input("Enter the campaign name to segment by: ")

# Initialize CreateSend client
cs = CreateSend({'api_key': API_KEY})
client = Client({'api_key': API_KEY}, CLIENT_ID)
campaign_objects = client.campaigns().__dict__['Results']

# Convert CreateSendModel objects to dicts
campaigns = [
    {
        'Name': c.Name,
        'CampaignID': c.CampaignID,
        'Subject': c.Subject,
        'SentDate': c.SentDate
    }
    for c in campaign_objects
]

# Step 1: Find the campaign
matching_campaign = None
for campaign in campaigns:
    if campaign_name_input.lower() in campaign['Name'].lower():
        matching_campaign = campaign
        break

if not matching_campaign:
    print("No matching campaign found.")
    exit()

campaign_id = matching_campaign['CampaignID']
campaign_name = matching_campaign['Name']
print(f"Found campaign: {campaign_name} ({campaign_id})")

# Step 2: Get lists the campaign was sent to
campaign = Campaign({'api_key': API_KEY}, campaign_id)

# Use correct method to fetch recipient lists
campaign_lists = campaign.lists_and_segments()

# Extract ListIDs
list_ids = [l.ListID for l in campaign_lists.Lists]

print("Lists this campaign was sent to:")
print(list_ids)

# Step 3: For each list, create a segment using CampaignNotOpened rule
segment_keyword = input("Enter the keyword for segments (*keyword* Resend: campaign_name): ")
for list_id in list_ids:
    list_details = List({'api_key': API_KEY}, list_id).details()
    list_name = list_details.Title

    segment_name = f"{segment_keyword} Resend: {campaign_name}"
    url = f"https://api.createsend.com/api/v3.3/segments/{list_id}.json"

    # Use supported RuleType: CampaignNotOpened
    payload = {
        "Title": segment_name,
        "RuleGroups": [
            {
                "Rules": [
                    {
                        "RuleType": "CampaignNotOpened",
                        "Clause": f"{campaign_id}"
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            url,
            auth=HTTPBasicAuth(API_KEY, ''),
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        if response.status_code == 201:
            print(f"Created segment '{segment_name}' in list '{list_name}'")
        else:
            print(f"Failed to create segment in list '{list_name}'")
    except Exception as e:
        print(f"Segment creation failed: {e}")
        import traceback
        traceback.print_exc()
