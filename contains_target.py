def contains_target(text, phrase):
    for i in phrase:
        if i.lower() in text.lower():
            return True
    return False