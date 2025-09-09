import time
import argparse
import tempfile
import shutil
from multiprocessing import Process
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- ROBUST SELECTORS (More reliable than absolute XPaths) ---
# Note: Zoom sometimes uses different IDs. These are the most common.
EMAIL_INPUT_ID = "input-for-email"
NAME_INPUT_ID = "input-for-name"
JOIN_BUTTON_SELECTOR = "button.join-btn" # A button with the class 'join-btn'

REAL_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36" # A Linux User-Agent is better for a Linux server
)

def join_zoom_webinar(zoom_link, email, display_name):
    bot_id = display_name
    print(f"[{bot_id}] STARTING...")

    user_data_dir = tempfile.mkdtemp(prefix=f"chrome_profile_{bot_id}_")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # The modern way to specify headless
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    chrome_options.add_argument("--use-fake-device-for-media-stream")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"user-agent={REAL_USER_AGENT}")
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # Use the pre-installed chromedriver path for stability on server
    # Ensure you ran `sudo mv chromedriver /usr/bin/chromedriver` in setup
    service = Service(executable_path="/usr/bin/chromedriver")
    driver = None

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Use the /j/ link, which is more reliable for triggering the web client flow
        print(f"[{bot_id}] Navigating to main join page...")
        driver.get(zoom_link)
        
        # --- RE-INTRODUCED: OUR PROVEN LOGIC ---
        # 1. Click "Join from browser" to trigger the web client page
        print(f"[{bot_id}] Looking for 'Join from browser' link...")
        join_browser_element = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Join from your browser"))
        )
        driver.execute_script("arguments[0].click();", join_browser_element)
        print(f"[{bot_id}] Clicked 'Join from browser'.")

        # 2. Switch to the iframe that contains the form
        print(f"[{bot_id}] Looking for iframe...")
        iframe = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        driver.switch_to.frame(iframe)
        print(f"[{bot_id}] Switched to iframe.")
        # --- END OF PROVEN LOGIC ---

        # Now, inside the iframe, find the elements by their robust IDs
        print(f"[{bot_id}] Looking for email input...")
        email_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, EMAIL_INPUT_ID))
        )
        email_input.send_keys(email)

        print(f"[{bot_id}] Looking for name input...")
        name_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, NAME_INPUT_ID))
        )
        name_input.send_keys(display_name)
        print(f"[{bot_id}] Details entered.")

        # Click Join
        join_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, JOIN_BUTTON_SELECTOR))
        )
        join_button.click()

        print(f"\n[SUCCESS] Bot {bot_id} has joined the webinar.\n")

        # Keep session alive
        while True:
            time.sleep(60)

    except Exception as e:
        print(f"\n[ERROR] Bot {bot_id} failed: {e}")
        if driver:
            ts = time.strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"error_{bot_id.replace(' ', '_')}_{ts}.png"
            page_source_path = f"page_{bot_id.replace(' ', '_')}_{ts}.html"
            driver.save_screenshot(screenshot_path)
            with open(page_source_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"[DEBUG] Evidence saved: {screenshot_path} and {page_source_path}")
    finally:
        if driver:
            driver.quit()
        shutil.rmtree(user_data_dir, ignore_errors=True)
        print(f"[{bot_id}] FINISHED. Browser closed and profile cleaned.")

def run_multiple_bots(zoom_link, base_email, base_name, count):
    processes = []
    for i in range(1, count + 1):
        email = base_email.replace("@", f"+{i}@")
        name = f"{base_name} {i}"
        p = Process(target=join_zoom_webinar, args=(zoom_link, email, name))
        processes.append(p)
        p.start()
        time.sleep(2) # Stagger launches

    for p in processes:
        p.join()

if __name__ == "__main__":
    # --- NOTE: Removed argparse for simplicity in this version ---
    # --- Hard-code the values for the server test ---
    ZOOM_URL = "https://us06web.zoom.us/j/85613807574?pwd=Jkh8FgMTxa3wKz3kz1bTNNVUaST39T.1"
    BASE_EMAIL = "kol@callistoinfotech.com"
    BASE_NAME = "Server Bot"
    BOT_COUNT = 1 # Start with 1 to test

    run_multiple_bots(ZOOM_URL, BASE_EMAIL, BASE_NAME, BOT_COUNT)