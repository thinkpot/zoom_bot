import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Main Configuration ---
ZOOM_LINK = "https://us06web.zoom.us/j/88679335956?pwd=MRn4M4QUCd6Nc1BI52utQgFe9jmJsU.1"
# We will use a base email and name, and add a number for each bot.
BASE_EMAIL = "shahid+testbot@callistoinfotech.com" # Using '+' is great for testing with Gmail
BASE_DISPLAY_NAME = "Test Bot"
NUMBER_OF_BOTS = 5 # The number of concurrent bots you want to run
STAY_IN_MEETING_SECONDS = 300 # Stay for 5 minutes

# --- XPaths ---
EMAIL_INPUT_XPATH = "//input[@id='input-for-email']"
NAME_INPUT_XPATH = "//input[@id='input-for-name']"

REAL_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)

# --- This is our main bot logic, now inside a function ---
def run_zoom_bot(bot_number):
    """
    Launches a single Selenium bot to join the Zoom meeting.
    `bot_number` is used to create a unique name and email.
    """
    display_name = f"{BASE_DISPLAY_NAME} {bot_number}"
    email_address = BASE_EMAIL.replace('@', f'+{bot_number}@')
    print(f"[Bot {bot_number}] STARTING - Name: {display_name}, Email: {email_address}")

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1280,800")
    # To save resources, we can run these in headless mode even locally
    # chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    chrome_options.add_argument("--use-fake-device-for-media-stream")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument(f"user-agent={REAL_USER_AGENT}")
    prefs = {"protocol_handler.excluded_schemes": {"zoommtg": False}}
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    driver = None

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(ZOOM_LINK)
        
        # Wait for "Join from browser" and click
        join_browser_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.LINK_TEXT, "Join from your browser")))
        driver.execute_script("arguments[0].click();", join_browser_element)

        # Switch to iframe
        iframe = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        driver.switch_to.frame(iframe)

        # Wait for fields
        email_input = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, EMAIL_INPUT_XPATH)))
        name_input = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, NAME_INPUT_XPATH)))
        
        # Enter details
        email_input.send_keys(email_address)
        name_input.send_keys(display_name)

        # Join
        join_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Join')]")))
        join_button.click()
        
        print(f"\n[Bot {bot_number}] SUCCESS! Joined the meeting. Will stay for {STAY_IN_MEETING_SECONDS} seconds.\n")
        
        # We replace the input() with a sleep, so the script can be automated
        time.sleep(STAY_IN_MEETING_SECONDS)

    except Exception as e:
        print(f"\n[Bot {bot_number}] ERROR: An error occurred: {e}\n")
        if driver:
            # Save a screenshot for the specific bot that failed
            driver.save_screenshot(f"error_bot_{bot_number}.png")

    finally:
        if driver:
            driver.quit()
            print(f"[Bot {bot_number}] FINISHED. Browser closed.")

# --- This is the main part of the script that starts the threads ---
if __name__ == "__main__":
    print(f"--- Starting test with {NUMBER_OF_BOTS} bots ---")
    threads = []

    # Create and start a thread for each bot
    for i in range(1, NUMBER_OF_BOTS + 1):
        thread = threading.Thread(target=run_zoom_bot, args=(i,))
        threads.append(thread)
        thread.start()
        time.sleep(2) # Stagger the joins slightly to look more natural

    # Wait for all threads (bots) to complete their tasks
    for thread in threads:
        thread.join()

    print("--- All bots have finished the test. ---")