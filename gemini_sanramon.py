import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import datetime

def download_san_ramon_agenda_packets(start_year, end_year, output_dir="san_ramon_agenda_packets"):
    """
    Downloads agenda packets from San Ramon's meeting calendar for specified years.

    Args:
        start_year (int): The starting year.
        end_year (int): The ending year.
        output_dir (str, optional): The directory to save the downloaded files. Defaults to "san_ramon_agenda_packets".
    """

    base_url = "https://sanramonca.iqm2.com/Citizens/Calendar.aspx"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            # Construct the URL for the specific year and month
            params = {"Year": year, "Month": month}
            url = f"{base_url}?{urllib.parse.urlencode(params)}"

            try:
                response = requests.get(url)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                soup = BeautifulSoup(response.content, "html.parser")

                # Find all meeting links
                meeting_links = soup.find_all("a", class_="RowLink")

                for link in meeting_links:
                    meeting_url = urllib.parse.urljoin(base_url, link["href"])
                    try:
                        meeting_response = requests.get(meeting_url)
                        meeting_response.raise_for_status()
                        meeting_soup = BeautifulSoup(meeting_response.content, "html.parser")

                        #find the meeting date.
                        meeting_date_element = meeting_soup.find("span", id="ContentPlaceHolder1_lblMeetingDate")
                        if meeting_date_element:
                            meeting_date_str = meeting_date_element.text.strip()
                            try:
                                meeting_date = datetime.datetime.strptime(meeting_date_str, "%B %d, %Y")
                                date_str = meeting_date.strftime("%Y-%m-%d")
                            except ValueError:
                                print(f"Warning: Could not parse meeting date: {meeting_date_str}")
                                date_str = "unknown_date"
                        else:
                            print(f"Warning: Meeting date not found for {meeting_url}")
                            date_str = "unknown_date"

                        # Find the Agenda Packet link
                        agenda_packet_link = meeting_soup.find("a", string=lambda text: text and "Agenda Packet" in text)

                        if agenda_packet_link:
                            packet_url = urllib.parse.urljoin(meeting_url, agenda_packet_link["href"])
                            packet_filename = f"{date_str}_SanRamon_AgendaPacket.pdf"
                            packet_filepath = os.path.join(output_dir, packet_filename)

                            try:
                                packet_response = requests.get(packet_url, stream=True)
                                packet_response.raise_for_status()

                                with open(packet_filepath, "wb") as f:
                                    for chunk in packet_response.iter_content(chunk_size=8192):
                                        f.write(chunk)

                                print(f"Downloaded: {packet_filename}")

                            except requests.exceptions.RequestException as e:
                                print(f"Error downloading {packet_filename}: {e}")
                        else:
                            print(f"No Agenda Packet found for {meeting_url}")

                    except requests.exceptions.RequestException as e:
                        print(f"Error accessing meeting details {meeting_url}: {e}")

            except requests.exceptions.RequestException as e:
                print(f"Error accessing calendar for {year}-{month}: {e}")

if __name__ == "__main__":
    start_year = 2024
    end_year = 2025
    download_san_ramon_agenda_packets(start_year, end_year)