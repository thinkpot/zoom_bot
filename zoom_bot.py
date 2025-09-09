import time
import argparse
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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

def start_browser_instance(user_email, user_name, bots_per_instance):
    # Create a unique temporary directory for each instance
    user_data_dir = tempfile.mkdtemp()

    # Set Chrome options
    chrome_options = Options()
    chrome_options.add_argument(f"user-data-dir={user_data_dir}")  # Unique user data dir for each bot
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,800")
    chrome_options.add_argument(f"user-agent={REAL_USER_AGENT}")
    # chrome_options.add_argument("--headless")  # Uncomment for headless mode if running on a server without display

    # Initialize the webdriver with Chrome options
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Navigate to the Zoom meeting page
        print(f"[INFO] Starting bot: {user_name} ({user_email})")
        driver.get("https://zoom.us/join")
        
        # Enter email
        email_input = driver.find_element(By.XPATH, EMAIL_INPUT_XPATH)
        email_input.clear()
        email_input.send_keys(user_email)

        # Enter name
        name_input = driver.find_element(By.XPATH, NAME_INPUT_XPATH)
        name_input.clear()
        name_input.send_keys(user_name)

        # Click Join
        join_button = driver.find_element(By.XPATH, "//button[contains(text(),'Join')]")
        driver.execute_script("arguments[0].scrollIntoView(true);", join_button)
        ActionChains(driver).move_to_element(join_button).click().perform()

        print(f"[SUCCESS] {user_name} joined the webinar.")

        # Keep the session alive for a while (or until manually stopped)
        while True:
            time.sleep(60)

    except Exception as e:
        print(f"[ERROR] {user_name} failed: {e}")
    finally:
        driver.quit()
        print(f"[INFO] Browser closed for {user_name}")

def run_multiple_bots(webinar_url, base_email, base_name, bots_per_instance, count):
    for i in range(count):
        # Create unique email for each bot (by appending a number to the base email)
        user_email = f"{base_email.split('@')[0]}+{i}@{base_email.split('@')[1]}"
        user_name = f"{base_name}_{i + 1}"

        start_browser_instance(user_email, user_name, bots_per_instance)

if __name__ == "__main__":
    # Command-line arguments for the script
    parser = argparse.ArgumentParser(description="Zoom Webinar Bot")
    parser.add_argument("--url", required=True, help="Zoom webinar/join link")
    parser.add_argument("--email", required=True, help="Base email (will be made unique)")
    parser.add_argument("--name", required=True, help="Base display name")
    parser.add_argument("--count", type=int, default=1, help="Number of bots to spawn on this machine")
    parser.add_argument("--bots-per-instance", type=int, default=5, help="Number of bots per instance")
    args = parser.parse_args()

    # Run the bots
    run_multiple_bots(args.url, args.email, args.name, args.bots_per_instance, args.count)
