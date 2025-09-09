import time
import argparse
from multiprocessing import Process
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import os
import tempfile
import shutil

# --- XPaths ---
EMAIL_INPUT_XPATH = "/html/body/div[2]/div[2]/div/div[1]/div/div/div[2]/div/input"
NAME_INPUT_XPATH = "/html/body/div[2]/div[2]/div/div[1]/div/div/div[3]/div/input"

REAL_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)

def slow_type(element, text, delay=0.05):
    """Type characters one by one with a small delay"""
    for char in text:
        element.send_keys(char)
        time.sleep(delay)

def join_zoom_webinar(zoom_link, email, display_name, process_id):
    print(f"[INFO] Starting bot: {display_name} ({email})")

    # Unique user data dir
    user_data_dir = tempfile.mkdtemp(prefix=f"chrome_profile_{display_name}_{process_id}_")
    print(f"[INFO] Using user data dir: {user_data_dir}")

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,800")
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    chrome_options.add_argument("--use-fake-device-for-media-stream")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument(f"user-agent={REAL_USER_AGENT}")
    chrome_options.add_experimental_option("prefs", {
        "protocol_handler.excluded_schemes": {"zoommtg": True},
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.popups": 2
    })
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Headless mode
    chrome_options.add_argument("--headless=new")  # new headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument("--remote-debugging-port=9222")

    service = Service(ChromeDriverManager().install())
    driver = None

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        direct_browser_url = zoom_link.replace("/j/", "/wc/join/")
        print(f"[INFO] Navigating to {direct_browser_url}")
        driver.get(direct_browser_url)

        # Wait until email input is present
        print("[INFO] Waiting for email input...")
        email_input = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, EMAIL_INPUT_XPATH))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", email_input)
        time.sleep(1)
        email_input.click()
        slow_type(email_input, email)

        # Wait for name input
        print("[INFO] Waiting for name input...")
        name_input = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, NAME_INPUT_XPATH))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", name_input)
        time.sleep(1)
        name_input.click()
        slow_type(name_input, display_name)

        # Click Join
        print("[INFO] Clicking Join button...")
        join_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Join')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", join_button)
        ActionChains(driver).move_to_element(join_button).click().perform()

        print(f"[SUCCESS] {display_name} joined the webinar.")

        # Keep session alive
        while True:
            time.sleep(60)

    except Exception as e:
        print(f"[ERROR] {display_name} failed: {e}")
        if driver:
            ts = time.strftime("%Y%m%d-%H%M%S")
            driver.save_screenshot(f"error_{display_name}_{ts}.png")
            with open(f"page_{display_name}_{ts}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
    finally:
        if driver:
            driver.quit()
            print(f"[INFO] Browser closed for {display_name}")
        shutil.rmtree(user_data_dir, ignore_errors=True)

def run_multiple_bots(zoom_link, base_email, base_name, count):
    processes = []
    for i in range(1, count + 1):
        email = base_email.replace("@", f"+{i}@")
        name = f"{base_name}_{i}"
        p = Process(target=join_zoom_webinar, args=(zoom_link, email, name, i))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zoom Webinar Bot")
    parser.add_argument("--url", required=True, help="Zoom webinar/join link")
    parser.add_argument("--email", required=True, help="Base email (will be made unique)")
    parser.add_argument("--name", required=True, help="Base display name")
    parser.add_argument("--count", type=int, default=1, help="Number of bots to spawn on this machine")
    args = parser.parse_args()

    run_multiple_bots(args.url, args.email, args.name, args.count)
