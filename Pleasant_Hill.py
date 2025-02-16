import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# URL of the web page
url = "https://pleasanthillca.iqm2.com/Citizens/calendar.aspx?From=1/1/2023&To=12/31/2025"

# Directory to save downloaded PDFs
download_dir = "downloaded_pdfs"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# Send a GET request to the web page
response = requests.get(url)
response.raise_for_status()  # Raise an error for bad status codes

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Find all anchor tags with href attributes
for link in soup.find_all('a', href=True):
    href = link['href']
    
    # Check if the link points to a PDF file
    if href.lower().endswith('.pdf'):
        # Construct the full URL
        pdf_url = urljoin(url, href)
        
        # Get the PDF file name
        pdf_name = os.path.basename(pdf_url)
        
        # Download the PDF file
        pdf_response = requests.get(pdf_url)
        pdf_response.raise_for_status()
        
        # Save the PDF file to the download directory
        with open(os.path.join(download_dir, pdf_name), 'wb') as pdf_file:
            pdf_file.write(pdf_response.content)
        
        print(f"Downloaded: {pdf_name}")

print("All PDFs downloaded.")
