import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from multiprocessing import Process

# --- Bot Configurations for 3 Bots ---
BOT_CONFIGS = [
    {
        "ZOOM_LINK": "https://us06web.zoom.us/j/88679335956?pwd=MRn4M4QUCd6Nc1BI52utQgFe9jmJsU.1",
        "EMAIL": "shahid@callistoinfotech.com",
        "DISPLAY_NAME": "Media Master Bot 1"
    },
    {
        "ZOOM_LINK": "https://us06web.zoom.us/j/88679335956?pwd=MRn4M4QUCd6Nc1BI52utQgFe9jmJsU.1",  # Same link for testing; adjust if different
        "EMAIL": "bot2@callistoinfotech.com",
        "DISPLAY_NAME": "Media Master Bot 2"
    },
    {
        "ZOOM_LINK": "https://us06web.zoom.us/j/88679335956?pwd=MRn4M4QUCd6Nc1BI52utQgFe9jmJsU.1",  # Same link for testing; adjust if different
        "EMAIL": "bot3@callistoinfotech.com",
        "DISPLAY_NAME": "Media Master Bot 3"
    }
]

# Specific XPaths for email and name input fields
EMAIL_INPUT_XPATH = "/html/body/div[2]/div[2]/div/div[1]/div/div/div[2]/div/input"
NAME_INPUT_XPATH = "/html/body/div[2]/div[2]/div/div[1]/div/div/div[3]/div/input"

REAL_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)

def join_zoom_webinar(bot_config):
    zoom_link = bot_config["ZOOM_LINK"]
    email = bot_config["EMAIL"]
    display_name = bot_config["DISPLAY_NAME"]
    print(f"[INFO] Starting bot for {display_name}...")
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1280,800")
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    chrome_options.add_argument("--use-fake-device-for-media-stream")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument(f"user-agent={REAL_USER_AGENT}")

    # Minimal protocol handler suppression
    prefs = {
        "protocol_handler.excluded_schemes": {"zoommtg": True},
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.popups": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(ChromeDriverManager().install())
    driver = None

    try:
        print(f"[INFO] Initializing WebDriver for {display_name}...")
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Use direct browser join URL
        direct_browser_url = zoom_link.replace("/j/", "/wc/join/")
        print(f"[INFO] Loading direct browser URL for {display_name}: {direct_browser_url}")
        driver.get(direct_browser_url)

        # Fallback: Handle any unexpected alerts
        try:
            print(f"[INFO] Checking for browser alert for {display_name}...")
            WebDriverWait(driver, 5).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.dismiss()
            print(f"[INFO] Dismissed unexpected alert for {display_name}.")
        except:
            print(f"[INFO] No browser alert detected for {display_name}.")

        # Debug input fields in main document
        print(f"[DEBUG] Checking for input fields in main document for {display_name}...")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"[DEBUG] Found {len(inputs)} input(s) in main document for {display_name}.")
        for i, inp in enumerate(inputs):
            print(f"[DEBUG] Input {i} for {display_name} - ID: {inp.get_attribute('id')}, Name: {inp.get_attribute('name')}, Type: {inp.get_attribute('type')}, Placeholder: {inp.get_attribute('placeholder')}")

        # Try locating fields in main document
        print(f"[INFO] Waiting for email input field for {display_name}...")
        email_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, EMAIL_INPUT_XPATH))
        )
        print(f"[INFO] Waiting for name input field for {display_name}...")
        name_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, NAME_INPUT_XPATH))
        )

        # Debug field values before entering data
        print(f"[DEBUG] Email field value before for {display_name}: ", email_input.get_attribute("value"))
        print(f"[DEBUG] Name field value before for {display_name}: ", name_input.get_attribute("value"))

        # Enter email
        retries = 0
        max_retries = 3
        while retries < max_retries:
            try:
                print(f"[INFO] Entering email for {display_name}...")
                email_input.clear()
                email_input.send_keys(email)
                break
            except Exception as e:
                print(f"[WARN] Failed to enter email for {display_name}. Retrying... ({e})")
                retries += 1
                time.sleep(2)
        if retries == max_retries:
            raise Exception(f"Failed to enter email for {display_name} after retries.")

        # Wait for any dynamic update after email entry
        print(f"[INFO] Waiting for name field to be ready for {display_name}...")
        WebDriverWait(driver, 5).until(
            lambda x: name_input.is_enabled() and name_input.is_displayed()
        )

        # Enter name
        retries = 0
        while retries < max_retries:
            try:
                print(f"[INFO] Entering name for {display_name}...")
                name_input.clear()
                name_input.send_keys(display_name)
                break
            except Exception as e:
                print(f"[WARN] Failed to enter name for {display_name}. Retrying... ({e})")
                retries += 1
                time.sleep(2)
        if retries == max_retries:
            raise Exception(f"Failed to enter name for {display_name} after retries.")

        # Debug field values after entering data
        print(f"[DEBUG] Email field value after for {display_name}: ", email_input.get_attribute("value"))
        print(f"[DEBUG] Name field value after for {display_name}: ", name_input.get_attribute("value"))

        # Click the Join button
        print(f"[INFO] Looking for the final join button for {display_name}...")
        join_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Join')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", join_button)
        actions = ActionChains(driver)
        actions.move_to_element(join_button).click().perform()
        print(f"[INFO] Final join button clicked for {display_name}.")

        print(f"\n[SUCCESS] Bot {display_name} has clicked the final join button!")
        print(f"         {display_name} should now be in the waiting room or in the webinar.")

        # Keep the session open
        while True:
            time.sleep(60)  # Keep browser open; press Ctrl+C to stop manually

    except Exception as e:
        print(f"\n[ERROR] An error occurred for {display_name}: {e}")
        if driver:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot_file = f"error_screenshot_{display_name}_{timestamp}.png"
            driver.save_screenshot(screenshot_file)
            print(f"[DEBUG] Screenshot saved as {screenshot_file} for {display_name}")
            with open(f"page_source_{display_name}_{timestamp}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"[DEBUG] Page source saved as page_source_{display_name}_{timestamp}.html")

    finally:
        if driver:
            driver.quit()
            print(f"[INFO] WebDriver closed for {display_name}.")

def run_multiple_bots():
    processes = []
    for bot_config in BOT_CONFIGS:
        p = Process(target=join_zoom_webinar, args=(bot_config,))
        processes.append(p)
        p.start()

    # Wait for all bots to finish
    for p in processes:
        p.join()

if __name__ == "__main__":
    run_multiple_bots()