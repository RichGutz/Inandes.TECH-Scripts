import os
import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def lookup_ruc_info(ruc: str) -> dict:
    """
    Looks up RUC information (name and address) from datosperu.org using Selenium.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"')

    driver = None
    name = "N/A"
    address = "N/A"

    try:
        driver_path_raw = ChromeDriverManager().install()
        chromedriver_executable_path = os.path.join(os.path.dirname(driver_path_raw), "chromedriver.exe")
        print(f"[DEBUG] Constructed ChromeDriver executable path: {chromedriver_executable_path}")
        service = Service(chromedriver_executable_path)
        driver = webdriver.Chrome(service=service, options=options)

        # Start with the search page to get the company name
        search_url = f"https://www.datosperu.org/buscador_empresas.php?buscar={ruc}"
        driver.get(search_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        soup_search = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract name from the search results page directly using regex on the entire text
        full_text_search = soup_search.get_text()
        name_match_search = re.search(f"(.*?)\\s*\\(RUC: {ruc}\\)", full_text_search, re.DOTALL)
        if name_match_search:
            name_from_search = name_match_search.group(1).strip()
            # Clean the name for URL slug (remove special chars, replace spaces with hyphens)
            name_slug = re.sub(r'[^a-zA-Z0-9 ]', '', name_from_search).replace(' ', '-').lower()
            
            # Construct the detailed page URL
            detailed_page_url = f"https://www.datosperu.org/empresa-{name_slug}-{ruc}.php"
            print(f"[DEBUG] Constructed detailed page URL: {detailed_page_url}")
            driver.get(detailed_page_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            soup_detailed = BeautifulSoup(driver.page_source, 'html.parser')

            # Extract name and address from the detailed page using regex on the text content
            detailed_text = soup_detailed.get_text()
            print(f"[DEBUG] Detailed Page Text for {ruc}:\n{detailed_text[:500]}...") # Print first 500 chars

            name_match = re.search(r'NOMBRE\\s*(.*?)(?:RUC|INICIO)', detailed_text, re.DOTALL)
            print(f"[DEBUG] Name Match for {ruc}: {name_match}")
            if name_match:
                name = name_match.group(1).strip()
            
            address_match = re.search(r'DIRECCIÓN\\s*(.*?)(?:DEPARTAMENTO|PAÍS|TELÉFONO)', detailed_text, re.DOTALL)
            print(f"[DEBUG] Address Match for {ruc}: {address_match}")
            if address_match:
                address = address_match.group(1).strip()

        return {"name": name, "address": address}

    except Exception as e:
        print(f"Error fetching RUC info for {ruc} with Selenium: {e}")
        return {"name": "Error", "address": "Error"}
    finally:
        if driver:
            time.sleep(1) # Give some time for the browser to close properly
            driver.quit()

if __name__ == '__main__':
    ruc_example = "20563361761"  # ZEN HOLDINGS SAC
    info = lookup_ruc_info(ruc_example)
    print(f"RUC: {ruc_example}, Name: {info['name']}, Address: {info['address']}")

    ruc_example_2 = "20600079070" # Example RUC that might not have a direct page
    info_2 = lookup_ruc_info(ruc_example_2)
    print(f"RUC: {ruc_example_2}, Name: {info_2['name']}, Address: {info_2['address']}")