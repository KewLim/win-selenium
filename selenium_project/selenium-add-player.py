import time
import re
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
from selenium.webdriver.support.ui import Select
from datetime import datetime
from collections import defaultdict
import re
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException


def wait_for_overlay_to_disappear(driver, max_wait=5):
    """Fast overlay detection - only wait if overlay actually exists"""
    overlay_selectors = [
        "div.absolute.inset-0.transition-opacity.duration-300.bg-slate-900\\/60",
        ".app-preloader",
        "div.app-preloader"
    ]
    
    overlay_found = False
    for selector in overlay_selectors:
        try:
            # Quick check if overlay exists
            overlays = driver.find_elements(By.CSS_SELECTOR, selector)
            if overlays and overlays[0].is_displayed():
                print(f"[INFO] {selector} overlay detected, waiting...")
                WebDriverWait(driver, max_wait).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
                )
                overlay_found = True
                print(f"[INFO] {selector} overlay disappeared")
        except:
            continue
    
    if overlay_found:
        time.sleep(0.3)  # Brief wait for DOM stability
        return True
    return False


def smart_click(element, verify_callback=None):
    """
    Smart click with minimal retries - only retry if overlay blocks
    """
    try:
        # Try normal click first
        element.click()
        
        # Quick verification if callback provided
        if verify_callback:
            time.sleep(0.3)
            if verify_callback():
                return True
            else:
                # Only retry if overlay is blocking
                if wait_for_overlay_to_disappear(driver, max_wait=3):
                    element.click()
                    time.sleep(0.3)
                    return verify_callback()
                return False
        return True
        
    except Exception as click_error:
        error_msg = str(click_error)
        # Only retry if it's an overlay blocking issue
        if "obscures it" in error_msg or "not clickable" in error_msg:
            print("[INFO] Overlay blocking click, trying JS click...")
            element.send_keys(Keys.ENTER)
            if wait_for_overlay_to_disappear(driver, max_wait=3):
                driver.execute_script("arguments[0].click();", element)
                if verify_callback:
                    time.sleep(0.3)
                    return verify_callback()
                return True
        raise click_error


options = Options()
# options.add_argument('--headless')  # Uncomment if you want headless mode

service = Service(GeckoDriverManager().install())
driver = webdriver.Firefox(service=service, options=options)
driver.maximize_window()



driver.get("https://www.rocketgo.asia/login")

wait = WebDriverWait(driver, 40)
merchant_input = wait.until(EC.presence_of_element_located((By.NAME, "merchant_code")))
merchant_input.send_keys("luckytaj")

wait = WebDriverWait(driver, 40)
username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
username_input.send_keys("Admin_Json")

wait = WebDriverWait(driver, 40)
password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
password_input.send_keys("json8888"+ Keys.ENTER)

try:
    WebDriverWait(driver, 20, poll_frequency=0.2).until_not(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.app-preloader")
        )
    )
    print("[INFO] Preloader disappeared.")
except TimeoutException:
    print("[WARN] Preloader still visible. Trying to proceed anyway...")

    time.sleep(1)


try:
    # Wait for the 'Players Management' link to be clickable
    players_link = WebDriverWait(driver, 20, poll_frequency=0.2).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Players Management"))
    )
    time.sleep(5)
    players_link.click()
    print("[INFO] Clicked on 'Players Management' link.")
except TimeoutException:
    print("[ERROR] Timed out waiting for 'Players Management' link.")


# --- Check Table load ---
wait = WebDriverWait(driver, 30)
table_presence = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "gridjs-tr")))
print("[INFO] Table loaded")






def load_phone_records_from_file():

    filename = "selenium_project/selenium-phone-number.txt"
    pattern = re.compile(r"#\d+\s+-\s+Phone:\s+(\d+),\s+Email:\s+(.*?),\s+Affiliate:\s+(.*)", re.IGNORECASE)
    records = []

    with open(filename, 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file if line.strip()][::-1]

    for line in lines:
        match = pattern.match(line)
        if match:
            phone, email, affiliate = (x.strip() for x in match.groups())
            records.append({
                "Phone Number": phone,
                "Email": email,
                "Affiliate Code": affiliate
            })
        else:
            print(f"⚠️ Skipping malformed line: {line}")

    return records







def add_player_details(record):

    """Fill Order ID, Phone Number, and Amount into form."""
    print(f"Processing Record: {record}")

    # Wait for any overlay to disappear
    try:
        WebDriverWait(driver, 10).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.absolute.inset-0"))
        )
        print("[INFO] Overlay disappeared")
    except TimeoutException:
        print("[WARN] Overlay still present, trying to proceed")

    time.sleep(1)
    wait = WebDriverWait(driver, 20)
    add_button = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//button[contains(text(), 'Add New Player')]"
    )))
    smart_click(add_button)
    print("[INFO] Add Player button clicked")

    time.sleep(1)

    # ===== Player ID =====

    player_id_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Player ID']"))
    )
    player_id_input.clear()
    player_id_input.send_keys(record["Phone Number"])
    print(f"[INFO] Player ID entered: {record['Phone Number']}")


    # ===== Phone Number =====

    number_id_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Phone Number']"))
    )
    number_id_input.clear()
    number_id_input.send_keys(record["Phone Number"])
    print(f"[INFO] Player ID entered: {record['Phone Number']}")


    # ===== Email =====
    if record["Email"] != "-":
        number_id_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Email']"))
        )
        number_id_input.clear()
        number_id_input.send_keys(record["Email"])
        print(f"[INFO] Email entered: {record['Email']}")
    else:
        print("[INFO] Skipped Email input (value was '-')")


    # ===== Affiliate Code =====

    number_id_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Enter affiliate name']"))
    )
    number_id_input.clear()
    number_id_input.send_keys(record["Affiliate Code"])
    print(f"[INFO] Player ID entered: {record['Affiliate Code']}")

    number_id_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Enter affiliate ID']"))
    )
    number_id_input.clear()
    number_id_input.send_keys(record["Affiliate Code"])
    print(f"[INFO] Player ID entered: {record['Affiliate Code']}")

    time.sleep(1)
    
    # Submit the form using Enter key
    try:
        # Find the last input field (affiliate ID) and press Enter
        last_input = driver.find_element(By.XPATH, "//input[@placeholder='Enter affiliate ID']")
        last_input.send_keys(Keys.ENTER)
        print("[INFO] Form submitted via Enter key")
    except Exception as e:
        print(f"[ERROR] Could not submit form with Enter key: {e}")
    
    time.sleep(2)





records = load_phone_records_from_file()

for record in records:
    add_player_details(record)

time.sleep(5)  
driver.quit()