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


# --------------------------------------------------------------
# robots.txt permission check
# --------------------------------------------------------------
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


# --------------------------------------------------------------
# start driver (headless)
# --------------------------------------------------------------
def setup_driver() -> webdriver.Firefox:
    if not check_permission(constants.URL, constants.USER_AGENT): 
        sys.exit("Robots.txt disallows crawling this URL.")
        
    service = Service(executable_path=constants.EXECUTABLE_PATH) 
    options = Options()
    options.add_argument("--headless")
    options.binary_location = constants.BINARY_PATH 
    driver = webdriver.Firefox(service=service, options=options) 
    
    return driver


# --------------------------------------------------------------
# grabs <body>
# --------------------------------------------------------------
def reach_website(driver: webdriver.Firefox) -> None:
    driver.get(constants.URL)   # reaches the website
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )


# --------------------------------------------------------------
# extracts body text
# --------------------------------------------------------------
def get_clean_body_text(driver: webdriver.Firefox) -> str:
    reach_website(driver)
    body = driver.find_element(By.TAG_NAME, "body")
    raw = body.text
    return re.sub(r"\s+", " ", raw).strip()


# --------------------------------------------------------------
# checking privacy policy and cookie consent
# --------------------------------------------------------------
def check_privacy_policy() -> None:
    driver = setup_driver()
    try:
        text = get_clean_body_text(driver)
        targets = ["Privacy Policy", "Política de privacidade"]
        ok = any(t.lower() in text.lower() for t in targets)
        print("Site presents privacy policy" if ok else "Site does NOT present privacy policy")
    finally:
        driver.quit()


def check_cookie_banner() -> None:
    driver = setup_driver()
    try:
        text = get_clean_body_text(driver).lower()
        has_cookie = ("cookie" in text or "cookies" in text)
        has_refuse = ("refuse" in text or "recusar" in text or "não aceitar" in text)
        ok = has_cookie and has_refuse
        print("Site offers a reject‑cookies option" if ok else "Site does NOT offer a reject‑cookies option")
    finally:
        driver.quit()


# --------------------------------------------------------------
# password strength check
# --------------------------------------------------------------
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


def check_password_strength() -> None:
    driver = setup_driver()
    try:
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
    finally:
        driver.quit()


# --------------------------------------------------------------
# check if cookies are collected before consent
# --------------------------------------------------------------
def check_consent_before_cookies(consent_locator):
    driver = setup_driver()
    try:
        driver.get(constants.URL)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # ----------- switch to iframe if necessary -----------
        try:
            iframe = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//iframe[contains(@src, 'consent') or contains(@src, 'cookie')]")
                )
            )
            driver.switch_to.frame(iframe)
            print("[Info] Switched to consent iframe.")
        except Exception:
            pass

        # ----------- PRE‑CONSENT snapshot ----------
        pre_js = driver.execute_script("return document.cookie;")
        pre_set = [
            r.headers.get("Set-Cookie")
            for r in driver.requests
            if r.response and r.headers.get("Set-Cookie")
        ]

        # ----------- CLICK THE CONSENT BUTTON ----------
        consent_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(consent_locator)
        )
        if consent_button:
            consent_button.click()
        else:
            sys.exit("\nO botão de aceitar cookies não foi encontrado\n")
        time.sleep(3)

        # ----------- POST‑CONSENT snapshot ----------
        post_js = driver.execute_script("return document.cookie;")
        post_set_all = [
            r.headers.get("Set-Cookie")
            for r in driver.requests
            if r.response and r.headers.get("Set-Cookie")
        ]
        post_set = [h for h in post_set_all if h not in pre_set]

        # ----------- RESULT ----------
        if not pre_js.strip() and not pre_set and (post_js.strip() or post_set):
            print("\nCookies are set ONLY AFTER consent.\n")
        elif pre_js.strip() or pre_set:
            print("\nCookies appear BEFORE consent.\n")
            print("Pre‑JS cookies :", pre_js)
            print("Pre‑Set‑Cookie headers :", pre_set)
            print("\nPost‑JS cookies :", post_js)
            print("Post‑Set‑Cookie headers :", post_set)
        else:
            print("\nℹNo cookies detected at all (maybe the site uses localStorage).\n")
    finally:
        driver.quit()


# --------------------------------------------------------------
# menu
# --------------------------------------------------------------
def menu():
    while True:
        choice = input(
            "O que você gostaria de buscar?"
            "\n1 - Política de privacidade"
            "\n2 - Opção de recusar coleta de cookies"
            "\n3 - Checagem de força de senha"
            "\n4 - Verificar se cookies são definidos só após consentimento"
            "\n0 - Sair\n-> "
        ).strip()

        if choice == "0":
            break
        elif choice == "1":
            check_privacy_policy()
        elif choice == "2":
            check_cookie_banner()
        elif choice == "3":
            check_password_strength()
        elif choice == "4":
            consent_locator = (By.XPATH, "//button[contains(.,'Accept')]")
            check_consent_before_cookies(consent_locator)
                
        else:
            print("\n!!! Opção inválida; escolha uma das opções listadas !!!\n")
