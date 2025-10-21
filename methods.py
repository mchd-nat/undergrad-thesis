import sys
import requests
import re

import urllib.robotparser
from urllib.parse import urlparse, urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

import constants

# checks if the target website allows web crawlers
def check_permission(url: str, user_agent: str = "*") -> bool:    
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(urljoin(base, "/robots.txt"))
    try:
        rp.read()
    except Exception:
        return False
    return rp.can_fetch(user_agent, url)

def setup_driver() -> webdriver.Firefox:
    if not check_permission(constants.URL, constants.USER_AGENT): 
        sys.exit("Robots.txt disallows crawling this URL.")
        
    service = Service(executable_path=constants.EXECUTABLE_PATH) 
    options = Options()
    options.binary_location = constants.BINARY_PATH 
    driver = webdriver.Firefox(service=service, options=options) 
    
    return driver

def reach_website(driver: webdriver.Firefox) -> webdriver.Firefox:
    driver.get(constants.URL)   # reaches the website
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    return driver

def clean_text(driver: webdriver.Firefox) -> str:
    driver = reach_website(driver)
    
    body = driver.find_elements(By.TAG_NAME, "body")
    raw_text = body[0].text
    cleaned = re.sub(r'\s+', ' ', raw_text).strip()
    
    return cleaned

### CHECKING FEATURES ###

def contains_target(text: str, phrase: list) -> bool:
    lower_case = text.lower()
    
    return any(i.lower() in lower_case for i in phrase)
    
def find_cookies_banner(text: str) -> bool:
    lower_case = text.lower()
    
    return (
        'cookie' in lower_case or 'cookies' in lower_case
        ) and (
            'refuse' in lower_case or 'recusar' in lower_case or 'não aceitar' in lower_case
        )

### PASSWORD STRENGTH CHECK ###

def get_strength_label(driver):
    label = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "#strength-meter .strength-label"))
    )
    return label.text.strip()

def get_strength_score(driver):
    pwd_elem = driver.find_element(By.ID, "pwd")
    score = pwd_elem.get_attribute("data-strength")
    if not score:
        score = driver.find_element(By.ID, "pwdScore").get_attribute("value")
    return int(score) if score else None

def get_zxcvbn_score(driver, pwd):
    script = """
        return typeof zxcvbn === 'function' ?
               zxcvbn(arguments[0]).score : null;
    """
    return driver.execute_script(script, pwd)    # returns None if library missing

def type_and_check_strength(driver, password, pwd_selector="#pwd"):
    pwd_input = driver.find_element(By.CSS_SELECTOR, pwd_selector)
    pwd_input.clear()
    pwd_input.send_keys(password)

    # Attempts to get info on the strength of the password
    try:
        return get_strength_label(driver)
    except Exception:
        pass

    try:
        return f"Score {get_strength_score(driver)}"
    except Exception:
        pass

    try:
        score = get_zxcvbn_score(driver, password)
        if score is not None:
            return f"Score {score}"
    except Exception:
        pass

    return "Unable to detect strength indicator"

### WEB CRAWLER PROPER ###

def crawler(choice: str):
    driver = setup_driver()
    
    try:
        if (choice == '1'):
            text = clean_text(driver)
            targets = ["Privacy Policy", "Política de privacidade"]
            print("Site presents privacy policy" if contains_target(text, targets) else "Site does NOT present privacy policy")
            
        elif choice == "2":
            text = clean_text(driver)
            print("Site presents option to refuse cookie collection" if find_cookies_banner(text) else "Site does NOT present option to refuse cookie collection")
            
        elif choice == "3":                   
            driver = reach_website(driver)    
            result = type_and_check_strength(driver, constants.PASSWORD, pwd_selector="#pwd")
            print("Password strength result:", result)
            
        else:
            print("\n!!! Opção inválida; escolha uma das opções listadas !!!\n")
            
    finally:
        driver.quit

### MENU ###

def menu():
    while True:
        choice = input(
            "O que você gostaria de buscar?"
            "\n1 - Política de privacidade"
            "\n2 - Opção de recusar coleta de cookies"
            "\n3 - Checagem de força de senha"
            "\n0 - Sair\n-> "
        ).strip()
        if choice == '0':
            break
        crawler(choice)