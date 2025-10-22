from flask import Flask, render_template, request, jsonify
from selenium.webdriver.common.by import By

import environment
import constants

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def print_symbol(is_check):
    if is_check: print('✔', end='  ') 
    else: print('✘', end='  ')

@app.route('/run-crawler', methods=['POST'])
def run_crawler():
    driver = None
    try: 
        data = request.get_json() or {}
        url = data.get('url', '')
        constants.url = url
        
        driver = environment.setup_driver()
        r = []
        
        has_privacy = environment.check_privacy_policy(driver)
        r.append({
            'check': 'Política de privacidade',
            'passed': has_privacy
        })
        
        has_cookie_option = environment.check_cookie_banner(driver)
        r.append({
            'check': 'Opção de recusar cookies',
            'passed': has_cookie_option
        })
        
        r.append(False)
        
        consent_locator = (By.XPATH, "//button[contains(.,'Accept')]")
        consent_check = environment.check_consent_before_cookies(consent_locator, driver)
        r.append({
            'check': 'Coleta de cookies somente após consentimento',
            'passed': consent_check if consent_check is not None else False
        })
        
        return jsonify({
            'success': True,
            'results': r
        })
        
    except Exception as err:
        return jsonify({
            'success': False,
            'error': str(err)
        }), 500
    finally:
        if driver:
            driver.quit()

# kickstarts the program
if __name__ == "__main__":
    app.run(debug=True, port=5000)

        

