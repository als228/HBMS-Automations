# HBMS-Automations
Algorithms created to reduce manual work and optimize work processes in HBMS (Historic Bethlehem Museums &amp; Sites) during my internship in Spring 2025

Three key algorithms to reduce manual labor: (1) data pipeline between Clover and Campaign Monitor, (2) campaign auto-resend, and (3) campaign analytics.
(1) Upload an excel file from Clover that has customer details. The algorithm extracts all customer details and automatically transfers to Campaign Monitor. Need CM API, Client ID, and List ID.
(2) Enter a campaign name. The algorithm finds it, then automatically creates new segments in all associated lists with customers who haven't opened the previous email. Functionally impossible to move further, because a template ID is needed to send a campaign with API - yet, custom templates don't have an assigned ID from Campaign Monitor. Thus, need to finish the last step manually - select the created segments and resend them.
(3) Create a service account in Google, then enter all information. Need to have CM API and Client ID as well. Then, all information about all campaigns in CM is transferred to a Google Spreadsheet, which makes analysis and reporting much easier (due to the confusing CM dashboard). 
