import re
import sys
import time
import urllib.robotparser
from urllib.parse import urlparse, urljoin

from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

import constants

# checks if the website's robots.txt allows scrapping
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

# starts the driver
def setup_driver() -> webdriver.Firefox:
    if not check_permission(constants.url, constants.USER_AGENT): 
        sys.exit("Robots.txt disallows crawling this URL.")
        
    service = Service(executable_path=constants.EXECUTABLE_PATH) 
    options = Options()
    options.add_argument("--headless")
    options.binary_location = constants.BINARY_PATH 
    driver = webdriver.Firefox(service=service, options=options) 
    
    return driver

# reaches out to the website and gets its body tag
def reach_website(driver: webdriver.Firefox) -> None:
    driver.get(constants.url)   # reaches the website
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

# extracts the raw text from the body tag
def get_clean_body_text(driver: webdriver.Firefox) -> str:
    reach_website(driver)
    body = driver.find_element(By.TAG_NAME, "body")
    raw = body.text
    return re.sub(r"\s+", " ", raw).strip()

# checking for the existence of a privacy policy and the ability to refuse cookies
def check_privacy_policy(driver) -> bool:
    text = get_clean_body_text(driver)
    print(text)
    targets = ["Privacy Policy", "Política de privacidade"]
    ok = any(t.lower() in text.lower() for t in targets)
    return ok

def check_cookie_banner(driver) -> bool:
    text = get_clean_body_text(driver).lower()
    has_cookie = ("cookie" in text or "cookies" in text)
    has_refuse = ("refuse" in text or "recusar" in text or "não aceitar" in text)
    ok = has_cookie and has_refuse
    return ok
    
# verifies whether or not the website checks for the strength of an inserted password
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
    return driver.execute_script(script, pwd)

def check_password_strength(driver) -> None:
    reach_website(driver)
    pwd_input = driver.find_element(By.CSS_SELECTOR, "#pwd")
    pwd_input.clear()
    pwd_input.send_keys(constants.PASSWORD)

    try:
        print("Strength label :", get_strength_label(driver))
        return
    except Exception:
        pass

    try:
        print("Strength score :", get_strength_score(driver))
        return
    except Exception:
        pass

    try:
        score = get_zxcvbn_score(driver, constants.PASSWORD)
        if score is not None:
            print("zxcvbn score :", score)
            return
    except Exception:
        pass

    print("Unable to detect a strength indicator.")

# check if cookies are collected before consent
def check_consent_before_cookies(consent_locator, driver):
    driver.get(constants.url)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    try:
        iframe = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//iframe[contains(@src, 'consent') or contains(@src, 'cookie')]")
            )
        )
        driver.switch_to.frame(iframe)
    except Exception:
        pass

    pre_js = driver.execute_script("return document.cookie;")
    pre_set = [
        r.headers.get("Set-Cookie")
        for r in driver.requests
        if r.response and r.headers.get("Set-Cookie")
    ]

    try:
        consent_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(consent_locator)
        )
        consent_button.click()
        time.sleep(3)
    except Exception:
        return False

    post_js = driver.execute_script("return document.cookie;")
    post_set_all = [
        r.headers.get("Set-Cookie")
        for r in driver.requests
        if r.response and r.headers.get("Set-Cookie")
    ]
    post_set = [h for h in post_set_all if h not in pre_set]

    if not pre_js.strip() and not pre_set and (post_js.strip() or post_set):
        return True
    elif pre_js.strip() or pre_set:
        return False
    else:
        return True

