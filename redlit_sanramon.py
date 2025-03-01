import logging
import os
from datetime import datetime
from pathlib import Path
import re
import time
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from download_utils import download_file, setup_download_directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "agenda_packets"

def get_agenda_items() -> List[Tuple[datetime, str, str]]:
    """Fetch agenda items using Selenium."""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    all_agenda_items = []

    try:
        logger.info("Starting Chrome WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)

        # Log Chrome version info
        logger.info("Chrome version: %s", driver.capabilities['browserVersion'])
        logger.info("ChromeDriver version: %s", driver.capabilities['chrome']['chromedriverVersion'])

        # Hardcoded URLs for San Ramon 2024 and 2025
        year_urls = {
            '2024': 'https://sanramonca.iqm2.com/Citizens/Calendar.aspx?View=List&From=1/1/2024&To=12/31/2024',
            '2025': 'https://sanramonca.iqm2.com/Citizens/Calendar.aspx?View=List&From=1/1/2025&To=12/31/2025'
        }

        for year, url in year_urls.items():
            try:
                logger.info(f"Accessing {year} calendar: {url}")
                driver.get(url)
                time.sleep(5)  # Initial wait for page load

                # Wait for table to be present
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "rgMasterTable"))
                )

                # Log page information for debugging
                logger.debug(f"Page title: {driver.title}")
                logger.debug(f"Current URL: {driver.current_url}")
                logger.debug("Page source snippet:")
                logger.debug(driver.page_source[:2000])

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                logger.info(f"Processing page source for {year}...")

                # Find meeting rows
                rows = soup.find_all('tr', class_=['rgRow', 'rgAltRow'])
                logger.info(f"Found {len(rows)} meeting rows for {year}")

                # Process each row
                for row_index, row in enumerate(rows, 1):
                    try:
                        logger.debug(f"\nProcessing row {row_index}:")
                        logger.debug(f"Row HTML: {row}")

                        # Get all cells in the row
                        cells = row.find_all('td')
                        if len(cells) < 2:
                            logger.warning(f"Row {row_index} has insufficient cells ({len(cells)}), skipping")
                            continue

                        # Get date from first cell
                        date_text = cells[0].get_text(strip=True)
                        if not re.match(r'\d{1,2}/\d{1,2}/\d{4}', date_text):
                            logger.warning(f"Row {row_index}: Invalid date format: {date_text}, skipping")
                            continue

                        meeting_date = datetime.strptime(date_text, '%m/%d/%Y')

                        # Get meeting type from second cell
                        meeting_type = cells[1].get_text(strip=True)
                        if not meeting_type:
                            meeting_type = "Unknown Meeting"
                            logger.warning(f"Row {row_index}: Empty meeting type, using default")

                        # Look for agenda packet links
                        found_packet = False
                        for cell_index, cell in enumerate(cells):
                            logger.debug(f"Checking cell {cell_index + 1} for links")
                            for link in cell.find_all('a'):
                                href = link.get('href', '')
                                text = link.get_text(strip=True)
                                logger.debug(f"Found link - href: {href}, text: {text}")

                                if 'FileOpen.aspx' in href and 'Type=1' in href:
                                    if not href.startswith('http'):
                                        href = f"https://sanramonca.iqm2.com/Citizens/{href.lstrip('/')}"
                                    logger.info(f"Found agenda packet: {meeting_date.strftime('%Y-%m-%d')} - {meeting_type}")
                                    all_agenda_items.append((meeting_date, meeting_type, href))
                                    found_packet = True
                                    break
                            if found_packet:
                                break

                        if not found_packet:
                            logger.warning(f"Row {row_index}: No agenda packet found for meeting on {meeting_date.strftime('%Y-%m-%d')}")

                    except Exception as e:
                        logger.error(f"Error processing row {row_index}: {str(e)}")
                        continue

            except Exception as e:
                logger.error(f"Error processing {year}: {str(e)}")
                continue

        logger.info(f"Total agenda items found: {len(all_agenda_items)}")
        return all_agenda_items

    except Exception as e:
        logger.error(f"Error in get_agenda_items: {str(e)}")
        return []
    finally:
        if 'driver' in locals():
            driver.quit()

def clean_filename(meeting_type: str) -> str:
    """Create clean filename from meeting type."""
    clean = re.sub(r'[<>:"/\\|?*]', '', meeting_type)
    clean = re.sub(r'\s+', '-', clean)
    clean = re.sub(r'-+', '-', clean)
    return clean.strip('-')

def main():
    """Main execution function."""
    try:
        # Setup download directory
        download_dir = setup_download_directory(DOWNLOAD_DIR)
        logger.info(f"Download directory created: {download_dir}")

        # Get agenda items
        logger.info("Fetching San Ramon meetings calendar...")
        agenda_items = get_agenda_items()

        if not agenda_items:
            logger.warning("No agenda packets found for 2024-2025")
            return

        logger.info(f"Found {len(agenda_items)} agenda packets to download")

        # Download each agenda packet
        for i, (date, meeting_type, url) in enumerate(agenda_items, 1):
            try:
                filename = f"{date.strftime('%Y-%m-%d')}_{clean_filename(meeting_type)}.pdf"
                filepath = download_dir / filename

                logger.info(f"[{i}/{len(agenda_items)}] Downloading: {filename}")
                logger.debug(f"URL: {url}")
                download_file(url, filepath)
                time.sleep(2)  # Delay between downloads

            except Exception as e:
                logger.error(f"Failed to download {url}: {str(e)}")
                continue

        logger.info("Download process completed")

    except Exception as e:
        logger.error(f"An error occurred during execution: {str(e)}")

if __name__ == "__main__":
    main()