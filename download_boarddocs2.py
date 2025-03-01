from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import requests
import time
import json

def download_pdfs_with_selenium():
    base_url = "https://go.boarddocs.com/ca/auhsd/Board.nsf/Public"
    output_dir = "auhsd_board_agendas"
    os.makedirs(output_dir, exist_ok=True)
    pdf_count = 0
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    
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
        time.sleep(5)  # Wait for JavaScript to render
        with open("initial_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Initial page source saved to 'initial_page.html'")
        
        wait = WebDriverWait(driver, 60)
        
        # Primary method: Find agenda links
        try:
            agenda_links = wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//a[contains(., 'Agenda')]")
                )
            )
            print(f"Found {len(agenda_links)} agenda links in rendered HTML")
            
            for i, agenda_link in enumerate(agenda_links):
                try:
                    parent = agenda_link.find_element(By.XPATH, "./ancestor::*[self::tr or self::div][1]")
                    date_text = None
                    for elem in parent.find_elements(By.XPATH, ".//*"):
                        text = elem.text.strip()
                        if text and ("2024" in text or "2025" in text):
                            date_text = text
                            break
                    
                    if not date_text:
                        print(f"Link {i}: No valid 2024/2025 date found, skipping")
                        continue
                    
                    agenda_url = agenda_link.get_attribute("href")
                    print(f"Link {i}: Found agenda for {date_text}: {agenda_url}")
                    
                    driver.execute_script(f"window.open('{agenda_url}');")
                    driver.switch_to.window(driver.window_handles[1])
                    
                    pdf_link = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '.pdf')]"))
                    )
                    pdf_url = pdf_link.get_attribute("href")
                    print(f"Link {i}: PDF URL: {pdf_url}")
                    
                    filename = f"agenda_{date_text.replace('/', '_')}.pdf"
                    filepath = os.path.join(output_dir, filename)
                    
                    print(f"Link {i}: Downloading: {filename}")
                    pdf_response = requests.get(pdf_url)
                    pdf_response.raise_for_status()
                    
                    with open(filepath, 'wb') as f:
                        f.write(pdf_response.content)
                    
                    pdf_count += 1
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Link {i}: Error processing agenda: {e}")
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    continue
                    
        except Exception as e:
            print(f"Failed to find agenda links in HTML: {e}")
            print("Falling back to JSON-LD parsing")
            
            # Fallback: Parse JSON-LD
            scripts = driver.find_elements(By.TAG_NAME, "script")
            json_found = False
            for i, script in enumerate(scripts):
                if "application/ld+json" in script.get_attribute("type"):
                    json_found = True
                    json_data = script.get_attribute("innerHTML")
                    try:
                        events = json.loads(json_data)
                        if not isinstance(events, list):
                            events = [events]
                        
                        print(f"Found {len(events)} events in JSON-LD")
                        for j, event in enumerate(events):
                            if event.get("@type") == "Event":
                                date_text = event.get("startDate", "").split("T")[0].replace("-", "/")
                                if "2024" not in date_text and "2025" not in date_text:
                                    print(f"Event {j}: Skipping {date_text} (not 2024/2025)")
                                    continue
                                
                                agenda_url = event.get("url")
                                print(f"Event {j}: Found agenda for {date_text}: {agenda_url}")
                                
                                driver.execute_script(f"window.open('{agenda_url}');")
                                driver.switch_to.window(driver.window_handles[1])
                                
                                pdf_link = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '.pdf')]"))
                                )
                                pdf_url = pdf_link.get_attribute("href")
                                print(f"Event {j}: PDF URL: {pdf_url}")
                                
                                filename = f"agenda_{date_text.replace('/', '_')}.pdf"
                                filepath = os.path.join(output_dir, filename)
                                
                                print(f"Event {j}: Downloading: {filename}")
                                pdf_response = requests.get(pdf_url)
                                pdf_response.raise_for_status()
                                
                                with open(filepath, 'wb') as f:
                                    f.write(pdf_response.content)
                                
                                pdf_count += 1
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                                time.sleep(1)
                                
                    except Exception as e:
                        print(f"Script {i}: Error processing JSON-LD: {e}")
                        if len(driver.window_handles) > 1:
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
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