from selenium.webdriver.common.by import By

import methods

def print_symbol(is_check):
    if is_check: print('✔', end='  ') 
    else: print('✘', end='  ')

# kickstarts the program
if __name__ == "__main__":
    driver = methods.setup_driver()
    try: 
        r = []
        
        r.append(methods.check_privacy_policy(driver))
        r.append(methods.check_cookie_banner(driver))
        r.append(False)
        consent_locator = (By.XPATH, "//button[contains(.,'Accept')]")
        c = methods.check_consent_before_cookies(consent_locator, driver)
        r.append(c)
        
        print('Website apresenta:\n')
        
        print_symbol(r[0])
        print('Política de privacidade')
        print_symbol(r[1])
        print('Opção de recusar a coleta de cookies')
        #print_symbol(r[2])
        #print('Checagem de força de senha')
        print_symbol(r[3])
        print('Coleta de cookies somente após o consentimento')
    finally:
        driver.quit()
        

