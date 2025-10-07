# @title List of Campaigns as calendar and analytics

"""
I use API code from Campaign Monitor (https://www.campaignmonitor.com/api/v3-3/getting-started/)
    AND Google API (Google Sheets & Google Drive).

INPUT:
  1. Nothing.
OUTPUT:
  1. Spreadsheet with all campaigns and their statistics.

Basically, data from all campaigns is shown in one spreadsheet. I go through all campaigns, collect their data,
then save it in the spreadsheet (using the Google API). The spreadsheet itself is premade with certain calculations
and formatting.

NOTE: don't forget to convert data type for date from TEXT to DATE in Google Sheets. Some formulas won't work otherwise.
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests
from datetime import datetime, timedelta

# 1. Campaign Monitor API setup
api_key = "###"
client_id = "###"

# 2. Pull sent campaigns
url_sent = f"https://api.createsend.com/api/v3.3/clients/{client_id}/campaigns.json"
response_sent = requests.get(url_sent, auth=(api_key, ''))
sent_campaigns_raw = response_sent.json()

sent_campaigns = []
for c in sent_campaigns_raw["Results"]:
    sent_campaigns.append({
        "Campaign Name": c["Name"],
        "Status": "Sent",
        "Date": c["SentDate"].split("T")[0]
    })

# 3. Pull scheduled campaigns
url_scheduled = f"https://api.createsend.com/api/v3.3/clients/{client_id}/scheduled.json"
response_scheduled = requests.get(url_scheduled, auth=(api_key, ''))
scheduled_campaigns_raw = response_scheduled.json()

scheduled_campaigns = []
for c in scheduled_campaigns_raw:
    scheduled_campaigns.append({
        "Campaign Name": c.get("Name", ""),
        "Status": "Scheduled",
        "Date": c.get("DateScheduled", "").split("T")[0]
    })

# 4. Get statistics on each campaign
campaigns_response = requests.get(
    f"https://api.createsend.com/api/v3.3/clients/{client_id}/campaigns.json", auth=(api_key, 'x')
)
campaigns = campaigns_response.json()

summaries = []
for campaign in campaigns['Results']:
    campaign_id = campaign['CampaignID']
    summary_response = requests.get(
        f"https://api.createsend.com/api/v3.3/campaigns/{campaign_id}/summary.json", auth=(api_key, 'x')
    )
    summary = summary_response.json()
    summary['Name'] = campaign['Name']  # Save the campaign name too
    summaries.append(summary)

# 4.a Get top 3 clicked links for each campaign
for i, campaign in enumerate(campaigns['Results']):
    campaign_id = campaign['CampaignID']
    url_clicks = f"https://api.createsend.com/api/v3.3/campaigns/{campaign_id}/clicks.json?pagesize=1000"
    response_clicks = requests.get(url_clicks, auth=(api_key, 'x'))

    try:
        clicks_data = response_clicks.json()
        link_clicks = {}

        for item in clicks_data.get('Results', []):
            url_clicked = item.get("URL")
            if url_clicked:
                link_clicks[url_clicked] = link_clicks.get(url_clicked, 0) + 1

        # Sort and take top 3
        top_links = sorted(link_clicks.items(), key=lambda x: x[1], reverse=True)[:3]

        for j in range(3):
            if j < len(top_links):
                link, count = top_links[j]
            else:
                link, count = "", 0  # Fallback for campaigns with <3 links

            sent_campaigns[i][f"Top Link {j+1}"] = f"{count} clicks on: {link}"

    except Exception as e:
        print(f"Error retrieving clicks for campaign {campaign_id}: {e}")
        sent_campaigns[i]["Top Link 1"] = "N/A"
        sent_campaigns[i]["Clicks on Link 1"] = 0

# calculate necessary values in the summaries list (i.e. list with a lot of statistic details)
for i in range(len(summaries)):
  sent_campaigns[i]['Total Recipients'] = summaries[i]['Recipients']
  sent_campaigns[i]['Open Rate'] = round(summaries[i]['UniqueOpened'] / summaries[i]['Recipients'], 2)
  sent_campaigns[i]['Click Rate'] = round(summaries[i]['Clicks'] / summaries[i]['Recipients'], 2)
  sent_campaigns[i]['Bounce Rate'] = round(summaries[i]['Bounced'] / summaries[i]['Recipients'], 2)
  sent_campaigns[i]['Spam Rate'] = round(summaries[i]['SpamComplaints'] / summaries[i]['Recipients'], 2)
  sent_campaigns[i]['Forward Rate'] = round(summaries[i]['Forwards'] / summaries[i]['Recipients'], 2)
  sent_campaigns[i]['Unsubscribe Rate'] = round(summaries[i]['Unsubscribed'] / summaries[i]['Recipients'], 2)
  sent_campaigns[i]['Unique Opens'] = summaries[i]['UniqueOpened']
  sent_campaigns[i]['Unique Clicks'] = summaries[i]['Clicks']
  sent_campaigns[i]['Bounces'] = summaries[i]['Bounced']
  sent_campaigns[i]['Spam Complaints'] = summaries[i]['SpamComplaints']
  sent_campaigns[i]['Forwards'] = summaries[i]['Forwards']
  sent_campaigns[i]['Unsubscribed'] = summaries[i]['Unsubscribed']

# 4. Combine both lists
combined_data = scheduled_campaigns + sent_campaigns
print(sent_campaigns_raw)
print(combined_data)

# 5. Connect to Google Sheets
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "###",
    "private_key_id": "###",
    "private_key": r"""-----BEGIN PRIVATE KEY-----
###
-----END PRIVATE KEY-----""",
    "client_email": "###",
    "client_id": "###",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "###",
    "universe_domain": "googleapis.com"
}

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

credentials = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gc = gspread.authorize(credentials)

# 6. Open your Google Sheet
spreadsheet = gc.open('Calendar of campaigns from CM')
worksheet = spreadsheet.worksheet('Summary')

# 7. Prepare dataframe
df = pd.DataFrame(combined_data)

# Separate 'Date' into 'Date' and 'Time'
df['Time'] = df['Date'].str.split(' ').str[1]
df['Date'] = df['Date'].str.split(' ').str[0]
df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%m/%d/%Y')
df['Date'] = df['Date'].str[1:]

# move 'Time' closer to beginning
column_to_move = df.pop('Time')
df.insert(3, 'Time', column_to_move)
# Move 'Top Link 1', 'Top Link 2', 'Top Link 3' right after 'Forward Rate'
after_column = 'Forward Rate'
insert_pos = df.columns.get_loc(after_column) + 1  # Insert after Forward Rate

for link_col in ['Top Link 1', 'Top Link 2', 'Top Link 3']:
    col_to_move = df.pop(link_col)
    df.insert(insert_pos, link_col, col_to_move)

# 8. Clear existing data
worksheet.clear()

# 9. Upload new data
if not df.empty:
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

print("Data updated successfully!")

# Convert Date to datetime and Unique Opens to numeric
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df['Unique Opens'] = pd.to_numeric(df['Unique Opens'], errors='coerce')

# Filter last 7 days and get top 5
cutoff = datetime.now() - timedelta(days=7)
recent_df = df[df['Date'] >= cutoff]
top5 = recent_df.sort_values('Unique Opens', ascending=False).head(5)
top5_out = top5[['Campaign Name', 'Date', 'Total Recipients', 'Unique Opens', 'Unique Clicks']]

# Create or clear worksheet
try:
    top5_sheet = spreadsheet.worksheet('Top 5 Campaigns for Last 7 Days')
    top5_sheet.clear()
except gspread.exceptions.WorksheetNotFound:
    top5_sheet = spreadsheet.add_worksheet(title='Top 5 Campaigns for Last 7 Days', rows=10, cols=5)

# Format date safely
top5_out['Date'] = top5_out['Date'].apply(
    lambda d: d.strftime('%m/%d/%Y') if pd.notnull(d) else ""
)

# Clean invalid values
top5_out.replace([float('inf'), float('-inf')], 0, inplace=True)
top5_out.fillna("", inplace=True)

# Upload to sheet
top5_sheet.update([top5_out.columns.values.tolist()] + top5_out.values.tolist())

print("Top 5 campaigns sheet updated successfully.")
