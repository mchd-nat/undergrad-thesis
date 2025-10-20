import main

def check_privacy_policy():
    main.setup("//div[contains(@class, 'política de privacidade') or contains(@class, 'politica de privacidade') or contains(@class, 'privacy policy') or contains(text(), 'política de privacidade')]", "privacy policy")