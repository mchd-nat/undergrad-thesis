import requests
import time
import constants
import privacy_policy
import cookies
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

def setup(x, element):
    service = Service(executable_path=constants.EXECUTABLE_PATH)
    
    options = Options()
    options.binary_location = constants.BINARY_PATH
    
    driver = webdriver.Firefox(service=service, options=options)
    
    try:
        driver.get(constants.URL)
        time.sleep(3)
        xpath = x
        found = driver.find_elements(By.XPATH, xpath)
        
        print("FOUND: " + found)
        
        if found:
            print("Site presents " + element)
        else:
            print("Site does not present " + element)
            
    except Exception as err:
        print((f"Error {constants.URL}: {err}"))
        
    finally:
        driver.quit()
    
def crawler(url):
    try:
        response = requests.get(url)
        response.raise_for_status # Throws an error if status is different than 200
        
        privacy_policy.check_privacy_policy()
        cookies.check_cookies()
    
    except Exception as err:
        print(f"Error trying to reach {url}: {err}")
        
crawler(constants.URL)
