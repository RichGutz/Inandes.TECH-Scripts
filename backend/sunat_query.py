import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_company_data_from_datosperu(ruc):
    """
    This function scrapes company data from datosperu.org using a RUC number
    with Selenium to handle potential anti-scraping measures.
    """
    if not ruc or not ruc.isdigit() or len(ruc) != 11:
        return {"error": "RUC inválido. Debe contener 11 dígitos."}

    search_url = f"https://www.datosperu.org/buscador_empresas.php?buscar={ruc}"
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = None
    try:
        service = ChromeService(executable_path=ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get(search_url)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "empresa"))
        )
        
        data = {}
        table = driver.find_element(By.CLASS_NAME, 'empresa')
        rows = table.find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, 'td')
            if len(cols) == 2:
                key = cols[0].text.strip().replace(':', '')
                value = cols[1].text.strip()
                data[key] = value

        if data:
            return data
        else:
            return {"error": "No se encontraron datos para el RUC proporcionado."}

    except Exception as e:
        return {"error": f"Ocurrió un error: {e}"}
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    # Example usage:
    ruc_to_search = "20563361761"
    company_data = get_company_data_from_datosperu(ruc_to_search)
    print(json.dumps(company_data, indent=4, ensure_ascii=False))