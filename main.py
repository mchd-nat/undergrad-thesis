import requests
import re
import time
import constants
import contains_target
import check_permission
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

choice =''

def target_element(no):
    target = ''
    if(no=='1'):
        target = ["Privacy Policy", "Política de privacidade"]
    elif(no=='2'):
        target = ["Cookies"]
    elif(no=='0'):
        exit
    else:
        print("\n\n!!! Escolha uma das opções na lista !!!\n\n")
        crawler(constants.URL, menu())
    return [no, target]

def menu():
    return target_element(input("O que você gostaria de buscar?\n1 - Política de privacidade\n2 - Opção de recusar coleta de cookies\n0 - Sair\n-> "))

def setup(element, target):
    if (check_permission.check_permission(constants.URL, constants.USER_AGENT) is False): 
        exit
        
    service = Service(executable_path=constants.EXECUTABLE_PATH)    # gets the driver
    options = Options()
    options.binary_location = constants.BINARY_PATH # reaches firefox
    driver = webdriver.Firefox(service=service, options=options)    # initiates the driver
    
    try:
        driver.get(constants.URL)   # reaches the website
        time.sleep(3)
        body = driver.find_elements(By.TAG_NAME, "body")
        raw_text = body[0].text
        cleaned = re.sub(r'\s+', ' ', raw_text).strip()
        
        found = contains_target.contains_target(cleaned, target)
        
        if found:
            print("Site presents", element)
        else:
            print("Site does not present", element)
            
    except Exception as err:
        print((f"Error {constants.URL}: {err}"))
        
    finally:
        driver.quit()
    
def crawler(url, target):
    try:
        response = requests.get(url)
        response.raise_for_status  
        
        if (target[0] == '1'):
            setup('privacy policy', target[1])
        elif (target[0] == '2'):
            setup('cookie banner', target[1])
    
    except Exception as err:
        print(f"Error trying to reach {url}: {err}")

# kickstarts the program
if __name__ == "__main__":   
    crawler(constants.URL, menu())
