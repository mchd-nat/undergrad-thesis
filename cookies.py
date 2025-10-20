import main

def check_cookies():
    main.setup("//div[contains(@class, 'cookie')]//button[contains(text(), 'recusar') or contains(text(), 'refuse') or contains(text(), 'non-essential') or contains(text(), 'non-essentials')]", "banner for cookies")