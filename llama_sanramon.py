import requests
from bs4 import BeautifulSoup
import os

# Send a GET request to the website
url = "https://sanramonca.iqm2.com/Citizens/Calendar.aspx"
try:
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
except requests.exceptions.RequestException as err:
    print(f"Error fetching URL: {err}")
    exit(1)

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Find all meeting dates
meeting_dates = soup.find_all('span', {'class': 'MeetingDate'})

if not meeting_dates:
    print("No meeting dates found on the webpage.")
    exit(1)

# Create a directory to store the agenda packets
agenda_packets_dir = 'agenda_packets'
if not os.path.exists(agenda_packets_dir):
    os.makedirs(agenda_packets_dir)

# Iterate over each meeting date
for date in meeting_dates:
    # Extract the meeting date and agenda packet URL
    meeting_date = date.text.strip()
    agenda_packet_url_tag = date.find_next('a')
    if agenda_packet_url_tag is None:
        print(f"Agenda packet URL not found for meeting date {meeting_date}.")
        continue
    agenda_packet_url = agenda_packet_url_tag['href']

    # Download the agenda packet
    try:
        agenda_packet_response = requests.get(agenda_packet_url)
        agenda_packet_response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as err:
        print(f"Error downloading agenda packet for {meeting_date}: {err}")
        continue

    agenda_packet_filename = f'{meeting_date}.pdf'
    agenda_packet_path = os.path.join(agenda_packets_dir, agenda_packet_filename)

    # Save the agenda packet to the directory
    try:
        with open(agenda_packet_path, 'wb') as f:
            f.write(agenda_packet_response.content)
        print(f'Downloaded agenda packet for {meeting_date}')
    except Exception as err:
        print(f"Error saving agenda packet for {meeting_date}: {err}")