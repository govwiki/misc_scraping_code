from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import os
import requests
import time
import json
import glob

def download_pdfs_with_selenium():
    base_url = "https://go.boarddocs.com/ca/auhsd/Board.nsf/Public"
    output_dir = "auhsd_board_agendas"
    os.makedirs(output_dir, exist_ok=True)
    pdf_count = 0
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    prefs = {
        "download.default_directory": os.path.abspath(output_dir),
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    chrome_driver_path = "C:/Windows/System32/chromedriver.exe"
    service = Service(executable_path=chrome_driver_path)
    service.log_path = "chromedriver.log"
    service.log_level = "INFO"
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("WebDriver initialized successfully")
    except Exception as e:
        print(f"Failed to initialize WebDriver: {e}")
        return
    
    try:
        driver.get(base_url)
        print("Page loaded")
        time.sleep(5)
        with open("initial_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Initial page source saved to 'initial_page.html'")
        
        # Fetch JSON-LD once and process events
        json_found = False
        scripts = driver.find_elements(By.TAG_NAME, "script")
        for script in scripts:
            if "application/ld+json" in script.get_attribute("type"):
                json_found = True
                json_data = script.get_attribute("innerHTML")
                print(f"JSON-LD: Found, length={len(json_data)} chars")
                try:
                    events = json.loads(json_data)
                    if not isinstance(events, list):
                        events = [events]
                    
                    print(f"Found {len(events)} events in JSON-LD")
                    for j, event in enumerate(events):  # Process all events
                        try:
                            if event.get("@type") == "Event":
                                date_text = event.get("startDate", "").split("T")[0].replace("-", "/")
                                if "2024" not in date_text and "2025" not in date_text:
                                    print(f"Event {j}: Skipping {date_text} (not 2024/2025)")
                                    continue
                                
                                agenda_url = event.get("url")
                                event_name = event.get("name", "Unknown_Event")
                                print(f"Event {j}: {event_name} on {date_text}, URL={agenda_url}")
                                
                                driver.get(agenda_url)
                                print(f"Event {j}: Navigated to agenda page")
                                time.sleep(3)
                                
                                try:
                                    download_button = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.ID, "btn-download-agenda-pdf"))
                                    )
                                    print(f"Event {j}: Found download button")
                                    
                                    driver.execute_script("arguments[0].click();", download_button)
                                    print(f"Event {j}: Clicked download button")
                                    time.sleep(10)
                                    
                                    filename = f"agenda_{date_text.replace('/', '_')}_{event_name.replace(' ', '_')}.pdf"
                                    filepath = os.path.join(output_dir, filename)
                                    print(f"Event {j}: Looking for {filename}")
                                    
                                    pdf_files = glob.glob(os.path.join(output_dir, "*.pdf"))
                                    if pdf_files:
                                        latest_pdf = max(pdf_files, key=os.path.getctime)
                                        print(f"Event {j}: Found PDF: {latest_pdf}")
                                        os.rename(latest_pdf, filepath)
                                        pdf_count += 1
                                    else:
                                        print(f"Event {j}: No PDF found in directory")
                                        with open(f"agenda_page_{j}.html", "w", encoding="utf-8") as f:
                                            f.write(driver.page_source)
                                        print(f"Event {j}: Saved agenda page to 'agenda_page_{j}.html'")
                                
                                except Exception as e:
                                    print(f"Event {j}: Failed to process download: {e}")
                                    with open(f"agenda_page_{j}.html", "w", encoding="utf-8") as f:
                                        f.write(driver.page_source)
                                    print(f"Event {j}: Saved agenda page to 'agenda_page_{j}.html'")
                                
                                # Return to base safely
                                driver.get(base_url)
                                time.sleep(2)
                        
                        except StaleElementReferenceException as e:
                            print(f"Event {j}: Stale element error, skipping: {e}")
                            driver.get(base_url)
                            time.sleep(2)
                        except Exception as e:
                            print(f"Event {j}: Unexpected error, skipping: {e}")
                            driver.get(base_url)
                            time.sleep(2)
                    
                    break  # Process only first JSON-LD
                
                except Exception as e:
                    print(f"JSON-LD: Error processing: {e}")
                    break
        if not json_found:
            print("No JSON-LD scripts found on page")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        with open("error_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Error page source saved to 'error_page.html'")
        
    finally:
        driver.quit()
        print(f"\nDownload complete. Total PDFs downloaded: {pdf_count}")

if __name__ == "__main__":
    import selenium
    print(f"Selenium version: {selenium.__version__}")
    download_pdfs_with_selenium()