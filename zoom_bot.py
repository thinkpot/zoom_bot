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

# --- XPaths ---
EMAIL_INPUT_XPATH = "/html/body/div[2]/div[2]/div/div[1]/div/div/div[2]/div/input"
NAME_INPUT_XPATH = "/html/body/div[2]/div[2]/div/div[1]/div/div/div[3]/div/input"

REAL_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)

def join_zoom_webinar(zoom_link, email, display_name):
    print(f"[INFO] Starting bot: {display_name} ({email})")

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

    service = Service(ChromeDriverManager().install())
    driver = None

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Force browser join
        direct_browser_url = zoom_link.replace("/j/", "/wc/join/")
        print(f"[INFO] Navigating to {direct_browser_url}")
        driver.get(direct_browser_url)

        # Dismiss popup if appears
        try:
            WebDriverWait(driver, 5).until(EC.alert_is_present())
            driver.switch_to.alert.dismiss()
        except:
            pass

        # Enter email
        email_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, EMAIL_INPUT_XPATH))
        )
        email_input.clear()
        email_input.send_keys(email)

        # Enter name
        name_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, NAME_INPUT_XPATH))
        )
        name_input.clear()
        name_input.send_keys(display_name)

        # Click Join
        join_button = WebDriverWait(driver, 10).until(
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

def run_multiple_bots(zoom_link, base_email, base_name, count):
    processes = []
    for i in range(1, count + 1):
        email = base_email.replace("@", f"+{i}@")  # unique emails
        name = f"{base_name}_{i}"
        p = Process(target=join_zoom_webinar, args=(zoom_link, email, name))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

if _name_ == "_main_":
    parser = argparse.ArgumentParser(description="Zoom Webinar Bot")
    parser.add_argument("--url", required=True, help="Zoom webinar/join link")
    parser.add_argument("--email", required=True, help="Base email (will be made unique)")
    parser.add_argument("--name", required=True, help="Base display name")
    parser.add_argument("--count", type=int, default=1, help="Number of bots to spawn on this machine")
    args = parser.parse_args()

    run_multiple_bots(args.url, args.email, args.name, args.count)

# Working