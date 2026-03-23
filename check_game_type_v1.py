from playwright.sync_api import sync_playwright
import re
import unicodedata

URL = input("CueScore URL: ").strip()

GAME_TYPE_PATTERNS = [
    (r"\b10[- ]?ball\b", "Bola 10"),
    (r"\b9[- ]?ball\b", "Bola 9"),
    (r"\b8[- ]?ball\b", "Bola 8"),
    (r"\bbola\s*10\b", "Bola 10"),
    (r"\bbola\s*9\b", "Bola 9"),
    (r"\bbola\s*8\b", "Bola 8"),
]

def strip_flags_and_symbols(text):
    if not text:
        return text
    out = []
    for ch in text:
        if unicodedata.category(ch).startswith("S"):
            continue
        out.append(ch)
    return "".join(out)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(URL, wait_until="domcontentloaded")
    text = page.locator("body").first.inner_text()
    text = strip_flags_and_symbols(text)
    found = None
    for pattern, label in GAME_TYPE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found = label
            break
    print("GAME TYPE:", found)
    print("--- BODY PREVIEW ---")
    print(text[:2000])
    input("Press Enter to close...")
    browser.close()
