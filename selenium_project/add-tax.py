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
from datetime import datetime, timedelta
from collections import defaultdict
import re
from selenium.webdriver import ActionChains


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
                if wait_for_overlay_to_disappear(driver, max_wait=5):
                    element.click()
                    time.sleep(0.3)
                    return verify_callback()
                return False
        return True
        
    except Exception as click_error:
        error_msg = str(click_error)
        # Check for overlay blocking issues
        if ("obscures it" in error_msg or "not clickable" in error_msg or 
            "app-preloader" in error_msg or "ElementClickInterceptedException" in str(type(click_error))):
            print(f"[INFO] Overlay blocking click: {error_msg}")
            
            # Wait for overlays to disappear
            if wait_for_overlay_to_disappear(driver, max_wait=10):
                print("[INFO] Overlays cleared, trying JS click...")
                try:
                    driver.execute_script("arguments[0].click();", element)
                    if verify_callback:
                        time.sleep(0.3)
                        return verify_callback()
                    return True
                except Exception as js_error:
                    print(f"[WARN] JS click also failed: {js_error}")
                    # Final fallback - scroll and try again
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.5)
                    element.click()
                    if verify_callback:
                        time.sleep(0.3)
                        return verify_callback()
                    return True
            else:
                print("[WARN] No overlays found but click still blocked")
        
        raise click_error


def reliable_click_with_locator(locator, max_attempts=3, delay=1, verify_callback=None):
    """
    Click element using locator to handle stale elements
    """
    for attempt in range(max_attempts):
        try:
            print(f"[INFO] Attempting click with locator (attempt {attempt + 1}/{max_attempts})")
            
            # Wait for any overlays to disappear
            wait_for_overlay_to_disappear(driver, max_wait=10)
            
            # Re-find element to avoid stale reference
            element = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable(locator)
            )
            
            # Scroll element into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(.5)
            
            # Try normal click first
            try:
                element.click()
                print("[INFO] Normal click successful")
            except Exception as click_error:
                print(f"[WARN] Normal click failed: {click_error}")
                # Fallback to JavaScript click
                print("[INFO] Trying JavaScript click...")
                driver.execute_script("arguments[0].click();", element)
                print("[INFO] JavaScript click successful")
            
            time.sleep(1)
            
            # If verification callback provided, use it
            if verify_callback and not verify_callback():
                if attempt < max_attempts - 1:
                    print(f"[WARN] Click verification failed, retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    print("[ERROR] Click verification failed after all attempts")
                    return False
            
            print("[INFO] Click successful")
            return True
            
        except Exception as e:
            print(f"[WARN] Click attempt {attempt + 1} failed: {e}")
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                print(f"[ERROR] All click attempts failed: {e}")
                raise e
    return False


def reliable_click(element, max_attempts=3, delay=1, verify_callback=None):
    """
    Click element with retry mechanism, overlay handling, and stale element recovery
    """
    for attempt in range(max_attempts):
        try:
            print(f"[INFO] Attempting click (attempt {attempt + 1}/{max_attempts})")
            
            # Wait for any overlays to disappear
            wait_for_overlay_to_disappear(driver, max_wait=10)
            
            # Scroll element into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(.5)
            
            # Try normal click first
            try:
                element.click()
                print("[INFO] Normal click successful")
            except Exception as click_error:
                print(f"[WARN] Normal click failed: {click_error}")
                # Fallback to JavaScript click
                print("[INFO] Trying JavaScript click...")
                driver.execute_script("arguments[0].click();", element)
                print("[INFO] JavaScript click successful")
            
            time.sleep(1)
            
            # If verification callback provided, use it
            if verify_callback and not verify_callback():
                if attempt < max_attempts - 1:
                    print(f"[WARN] Click verification failed, retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    print("[ERROR] Click verification failed after all attempts")
                    return False
            
            print("[INFO] Click successful")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"[WARN] Click attempt {attempt + 1} failed: {e}")
            
            # Check if it's a stale element error
            if "stale" in error_msg.lower() or "not connected to the DOM" in error_msg:
                print("[WARN] Stale element detected - element needs to be re-found")
                
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                print(f"[ERROR] All click attempts failed: {e}")
                raise e
    return False


def verify_dropdown_opened(driver):
    """Verify dropdown is opened by checking for dropdown options"""
    try:
        dropdown_options = driver.find_elements(By.CSS_SELECTOR, ".ts-dropdown, .dropdown-menu, [role='listbox']")
        return len(dropdown_options) > 0
    except:
        return False


def verify_modal_opened(driver):
    """Quick modal verification"""
    try:
        modal = driver.find_elements(By.CSS_SELECTOR, 
            ".flex.justify-between.px-4.py-3.rounded-t-lg.bg-slate-200.dark\\:bg-navy-800.sm\\:px-5")
        return len(modal) > 0 and modal[0].is_displayed()
    except:
        return False


def verify_calendar_opened(driver):
    """Verify calendar popup is opened"""
    try:
        calendar = driver.find_elements(By.CLASS_NAME, "flatpickr-calendar")
        return len(calendar) > 0 and "open" in calendar[0].get_attribute("class")
    except:
        return False





profile_path = "/Users/admin/Library/Application Support/Firefox/Profiles/7oz304au.default-release"
firefox_profile = webdriver.FirefoxProfile(profile_path)

options = Options()
options.set_preference("profile", profile_path)
# Optional: Use a separate Firefox profile
# Replace 'selenium-profile' with the name of a Firefox profile you’ve created
# or comment out if you want a fresh profile every time
# options.profile = "/Users/admin/Library/Application Support/Firefox/Profiles/xxxxxxxx.selenium-profile"

# Headless mode if needed
# options.add_argument('--headless')

# Setup the driver
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



def remove_bom(line):
    BOM = '\ufeff'
    if line.startswith(BOM):
        return line.lstrip(BOM)
    return line



def gateway_setup_movement(gateway_name):
    print(f"\033[93m[Gateway Setup] Executing setup for {gateway_name}\033[0m")

    gateway_map = {
        "XYPAY": "XYPAY",
        "XCPAY": "XCPAY",
        "SKPAY": "SKPAY",
        "YTPAY": "YTPAY",
        "OSPAY": "OSPAY",
        "SIMPLYPAY": "SIMPLYPAY",
        "VADERPAY": "VADERPAY",
        "PASSPAY": "PASSPAY",
        "MULTIPAY": "MULTIPAY",
        "U9PAY": "U9PAY",
        "BOMBAYPAY": "BOMBAYPAY",
        "EPAY": "EPAY",
        "MOHAMMED AMEER ABBAS": "Karnataka Bank 2",
        "Test": "Test",
        "Test2" : "Test2",
        "BOPAY": "BOPAY"
    }

    if gateway_name in gateway_map:
        enter_gateway_name(gateway_map[gateway_name])



def enter_gateway_name(gateway_text):
    # Step 1: Wait for preloader to disappear
    WebDriverWait(driver, 30).until(
        EC.invisibility_of_element_located((By.CLASS_NAME, "app-preloader"))
    )

    # Step 2: Click container to open dropdown using locator-based approach
    time.sleep(0.2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.3)  # Optional: wait for any sticky headers to settle
    
    # Use locator-based reliable click to handle stale elements
    container_locator = (By.CSS_SELECTOR, "div.ts-control")
    # Click dropdown container to open it
    container = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ts-control"))
    )
    smart_click(container, verify_callback=lambda: verify_dropdown_opened(driver))
    time.sleep(0.2)

    # Step 3: Find actual input (not always interactable)
    gateway_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "selectBank-ts-control"))
    )

    # Optional: Scroll it into view
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", gateway_input)
    time.sleep(0.1)

    print("Displayed:", gateway_input.is_displayed())
    print("Enabled:", gateway_input.is_enabled())
    print("Size:", gateway_input.size)
    print("Location:", gateway_input.location)

    try:
        # Try normal input method first
        gateway_input.send_keys(gateway_text)
    except Exception as e:
        print(f"[WARN] Normal input failed, using JS. Reason: {e}")
        # Fallback to JS-based input
        driver.execute_script("""
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        """, gateway_input, gateway_text)

    time.sleep(1)  # Wait for dropdown options

    # Step 4: Check if dropdown has valid options before selection
    try:
        # Check for dropdown options
        dropdown_options = driver.find_elements(By.CSS_SELECTOR, ".ts-dropdown .option, .ts-dropdown-content .option, [data-selectable='true'], .dropdown-item")
        
        if len(dropdown_options) == 0:
            print("[WARN] No dropdown options found, checking for alternative selectors...")
            # Try alternative selectors for dropdown options
            alternative_selectors = [
                ".ts-dropdown [data-value]",
                ".dropdown-menu li",
                ".select-dropdown li",
                "[role='option']",
                ".ts-dropdown > div"
            ]
            
            for selector in alternative_selectors:
                dropdown_options = driver.find_elements(By.CSS_SELECTOR, selector)
                if len(dropdown_options) > 0:
                    print(f"[INFO] Found {len(dropdown_options)} options with selector: {selector}")
                    break
        
        if len(dropdown_options) > 0:
            print(f"[INFO] Found {len(dropdown_options)} dropdown options")
            # Press Enter to select the first matching option
            gateway_input.send_keys(Keys.ENTER)
            print(f"[INFO] Gateway '{gateway_text}' entered and selected.")
        else:
            print("[WARN] No dropdown options available - the dropdown might be undefined/empty")
            print("[INFO] Trying to proceed without selection...")
            # Try pressing Enter anyway in case the input is accepted
            gateway_input.send_keys(Keys.ENTER)
            print(f"[INFO] Attempted to enter '{gateway_text}' without dropdown options.")
            
    except Exception as e:
        print(f"[WARN] Error checking dropdown options: {e}")
        # Fallback - try pressing Enter anyway
        gateway_input.send_keys(Keys.ENTER)
        print(f"[INFO] Fallback: Attempted to enter '{gateway_text}'.")
    
    time.sleep(0.5)





    # --- Check Table load with multiple selectors ---
    print("[INFO] Waiting for table to load...")
    table_selectors = [
        (By.CLASS_NAME, "gridjs-wrapper"),
        (By.CSS_SELECTOR, ".gridjs-wrapper"),
        (By.CSS_SELECTOR, "table"),
        (By.CSS_SELECTOR, ".table"),
        (By.CSS_SELECTOR, "[role='table']"),
        (By.CSS_SELECTOR, ".data-table"),
        (By.CSS_SELECTOR, ".grid-table")
    ]
    
    table_loaded = False
    wait = WebDriverWait(driver, 45)  # Increased timeout
    
    for selector in table_selectors:
        try:
            wait.until(EC.presence_of_element_located(selector))
            print(f"[INFO] Table loaded with selector: {selector}")
            table_loaded = True
            break
        except Exception as e:
            print(f"[DEBUG] Table selector {selector} failed: {e}")
            continue
    
    if not table_loaded:
        print("[WARN] Table loading timeout - proceeding anyway")
    
    time.sleep(1)  # Additional wait for table content to populate


# ======== Add Details HERE =======


def add_transaction_details(record):
    """Fill transaction details for tax records with Bank Charge selection."""
    print(f"Processing Tax Record: {record}")

    # Wait briefly for page load
    time.sleep(1)
    
    # Find Add button quickly
    wait = WebDriverWait(driver, 20)
    add_button = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//button[contains(text(), 'Add New Bank Transaction')]"
    )))
    
    # Single smart click with modal verification
    smart_click(add_button, verify_callback=lambda: verify_modal_opened(driver))
    print("[INFO] Add Transaction button clicked")

    # ===== Transaction Out =====
    
    # Find and click radio button quickly
    wait = WebDriverWait(driver, 15)
    out_radio = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="radio"][value="out"]'))
    )
    
    smart_click(out_radio)
    print("[INFO] Clicked 'out' radio button")

    # ===== Bank Charge Selection (NEW) =====
    try:
        print("[INFO] Attempting to change GAME to Bank Charge in combobox...")
        
        # Step 1: Click on the GAME item to open dropdown
        game_item_selectors = [
            'div[data-value="GAME"][data-ts-item]',
            '.ts-control div[data-value="GAME"]',
            '.item[data-value="GAME"]',
            'div.item[data-value="GAME"]'
        ]
        
        dropdown_opened = False
        for selector in game_item_selectors:
            try:
                game_item = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                smart_click(game_item)
                print(f"[INFO] Clicked GAME item using selector: {selector}")
                dropdown_opened = True
                time.sleep(.5)
                break
            except:
                continue
        
        # Step 2: If GAME item click failed, try clicking the entire control
        if not dropdown_opened:
            try:
                ts_control = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".ts-control"))
                )
                smart_click(ts_control)
                print("[INFO] Clicked .ts-control to open dropdown")
                dropdown_opened = True
                time.sleep(.5)
            except:
                pass
        
        # Step 3: If still not opened, try the input field
        if not dropdown_opened:
            try:
                input_field = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#tomselect-3-ts-control"))
                )
                smart_click(input_field)
                print("[INFO] Clicked input field to open dropdown")
                time.sleep(.5)
            except:
                print("[ERROR] Could not open dropdown")
        
        # Step 4: Wait for dropdown to appear and become visible
        try:
            dropdown = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".ts-dropdown"))
            )
            # Check if dropdown is visible (not display: none)
            if dropdown.is_displayed():
                print("[INFO] Dropdown is visible")
            else:
                print("[WARN] Dropdown exists but not visible")
        except:
            print("[WARN] Dropdown not found")
        
        # Step 5: Look for and click Bank Charge option
        print("[INFO] Searching for Bank Charge option...")
        bank_charge_selectors = [
            '.ts-dropdown-content div[data-value="Bank Charge"]',
            '.ts-dropdown div[data-value="Bank Charge"]',
            'div[data-value="Bank Charge"]',
            '.ts-dropdown .option[data-value="Bank Charge"]',
            '//div[contains(@class, "ts-dropdown")]//div[text()="Bank Charge"]',
            '//div[contains(@class, "ts-dropdown-content")]//div[text()="Bank Charge"]',
            '//*[contains(text(), "Bank Charge") and contains(@class, "option")]',
            '//*[contains(text(), "Bank Charge")]'
        ]
        
        bank_charge_selected = False
        for selector in bank_charge_selectors:
            try:
                if selector.startswith("//"):
                    bank_charge_option = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    bank_charge_option = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                time.sleep(1.5)
                smart_click(bank_charge_option)
                print(f"[INFO] ✅ Selected Bank Charge using selector: {selector}")
                bank_charge_selected = True
                time.sleep(.5)
                break
            except:
                continue
        
        if not bank_charge_selected:
            print("[ERROR] ❌ Could not find or select Bank Charge option")
        
    except Exception as e:
        print(f"[ERROR] Bank Charge selection failed: {e}")

    # ===== Bank Reference =====
    bank_reference_input = WebDriverWait(driver, 8).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Bank Reference']"))
    )

    # Force scroll into view before clear and type
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", bank_reference_input)
    time.sleep(2.1)

    bank_reference_input.clear()
    bank_reference_input.send_keys(record["Bank Reference"])
    print(f"[INFO] Bank Reference entered: {record['Bank Reference']}")

    # ===== Remarks Field (NEW) =====
    try:
        # Try multiple selectors for textarea Remarks field
        remarks_selectors = [
            "//textarea[@placeholder='Remarks']",
            "textarea[placeholder='Remarks']",
            "textarea[x-model='formData.remarks']",
            "//textarea[contains(@class, 'form-textarea')]",
            "textarea.form-textarea"
        ]
        
        remarks_input = None
        for selector in remarks_selectors:
            try:
                if selector.startswith("//"):
                    remarks_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                else:
                    remarks_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                print(f"[INFO] Found Remarks field with selector: {selector}")
                break
            except:
                continue
        
        if remarks_input:
            remarks_input.clear()
            remarks_input.send_keys(record["Remarks"])
            print(f"[INFO] Remarks entered: {record['Remarks']}")
        else:
            print("[WARN] Could not find Remarks textarea field")
            
    except Exception as e:
        print(f"[WARN] Error with Remarks field: {e}")

    # ===== Amount =====
    amount_input = WebDriverWait(driver, 8).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='amount']"))
    )
    amount_input.clear()
    amount_input.send_keys(str(record["Amount"]).replace(",", ""))
    print(f"[INFO] Amount entered: {record['Amount']}")

    # ===== Datepicker =====
    calendar_input = WebDriverWait(driver, 8).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Choose datetime...']"))
    )
    
    # Use reliable click with calendar verification
    smart_click(calendar_input, verify_callback=lambda: verify_calendar_opened(driver))
    print(f"[INFO] Calendar input clicked...")

    calendar_popup = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "flatpickr-calendar"))
    )

    if "open" in calendar_popup.get_attribute("class"):
        print("[INFO] Calendar popup is OPEN")

        target_date = record["Datetime"].strftime("%B %-d, %Y")  # e.g. "July 30, 2025"
        all_days = driver.find_elements(By.CSS_SELECTOR, ".flatpickr-day")

        for day in all_days:
            if day.get_attribute("aria-label") == target_date:
                driver.execute_script("arguments[0].scrollIntoView(true);", day)
                # Use reliable click for date selection
                smart_click(day)
                print(f"[INFO] Clicked date: {target_date}")
                break
        else:
            print(f"[ERROR] Date '{target_date}' not found in picker.")
    else:
        print("[WARN] Calendar popup did NOT open")

    # ===== Hour =====
    hour_input = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.flatpickr-hour")))
    hour_input.clear()
    hour_input.send_keys(record["Hour"])
    print(f"[INFO] Hour set to: {record['Hour']}")

    # ===== Minutes =====
    minute_input = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.flatpickr-minute")))
    minute_input.clear()
    minute_input.send_keys(record["Minute"])
    print(f"[INFO] Minute set to: {record['Minute']}")

    # ===== Decide AM or PM from the record =====
    ampm_target = "AM" if int(record.get("Hour", 0)) < 12 else "PM"
    ampm_toggle = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "flatpickr-am-pm"))
    )

    # Check and click if needed
    current_ampm = ampm_toggle.text.strip().upper()
    if current_ampm != ampm_target:
        # Use reliable click for AM/PM toggle
        smart_click(ampm_toggle)
        print(f"[INFO] AM/PM toggled to {ampm_target}")
    else:
        print(f"[INFO] AM/PM already set to {ampm_target}")

    # Confirm calendar selection by pressing Enter on the calendar input or body
    try:
        # First try to press Enter on the calendar input to confirm the datetime selection
        calendar_input = driver.find_element(By.XPATH, "//input[@placeholder='Choose datetime...']")
        calendar_input.send_keys(Keys.ENTER)
        print("[INFO] Calendar selection confirmed via Enter on calendar input")
    except Exception as e:
        print(f"[WARN] Could not confirm calendar via input: {e}")
        # Fallback: press Enter on body to confirm calendar
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ENTER)
            print("[INFO] Calendar selection confirmed via Enter on body")
        except Exception as e2:
            print(f"[WARN] Could not confirm calendar: {e2}")
    
    time.sleep(0.2)
    
    # Submit the form by finding and clicking the submit button
    try:
        submit_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit') or contains(text(), 'Save') or contains(text(), 'Add') or @type='submit']"))
        )
        smart_click(submit_button)
        print("[INFO] Form submitted via submit button")
    except Exception as e:
        print(f"[WARN] Could not find submit button, trying alternative approaches: {e}")
        # Fallback: try to submit form using Enter key on a form element
        try:
            form_inputs = driver.find_elements(By.CSS_SELECTOR, "input, textarea")
            if form_inputs:
                form_inputs[0].send_keys(Keys.ENTER)
                print("[INFO] Form submitted via Enter key on input")
        except Exception as e2:
            print(f"[ERROR] Could not submit form: {e2}")
    
    time.sleep(0.2)










def parse_and_execute(filename):
    """
    Parse both selenium-transaction_history.txt and wd-selenium-transaction_history.txt
    and extract tax values after '==== GRAND TOTAL' for each payment gateway.
    Create transaction records with proper placeholders and dynamic dates.
    """
    
    files_to_parse = [
        "selenium_project/selenium-transaction_history.txt",
        "selenium_project/wd-selenium-transaction_history.txt"
    ]
    
    transaction_records = []
    performed_gateways = set()
    
    supported_gateways = {
        "XYPAY", "SKPAY", "YTPAY", "OSPAY", "SIMPLYPAY", "VADERPAY",
        "PASSPAY", "MULTIPAY", "U9PAY", "BOMBAYPAY", "EPAY", 
        "MOHAMMED AMEER ABBAS", "Test", "Test2", "BOPAY", "XCPAY"
    }
    
    for file_path in files_to_parse:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find the section after "==== GRAND TOTAL"
            grand_total_match = re.search(r'==== GRAND TOTAL.*?\n+(.*)', content, re.DOTALL)
            
            if grand_total_match:
                tax_section = grand_total_match.group(1)
                
                # Extract individual gateway tax lines with label and date
                # Pattern matches: "(depo) pg SKPAY 29/07/2025 | Total Fee: Rs 3739.20"
                # or "(wd) pg XYPAY 29/07/2025 | Total Fee: Rs 54.00"
                tax_pattern = r'\((\w+)\)\s+pg\s+([A-Z0-9a-z]+)\s+([\d/]+)\s+\|\s+Total Fee:\s+Rs\s+([\d,]+\.?\d*)'
                matches = re.findall(tax_pattern, tax_section)
                
                for label, gateway, tax_date, tax_amount in matches:
                    # Only process supported gateways
                    if gateway not in supported_gateways:
                        print(f"[WARNING] Unsupported gateway '{gateway}', skipping.")
                        continue
                        
                    # Convert tax amount to float, removing commas
                    tax_value = float(tax_amount.replace(',', ''))
                    
                    # Parse tax date and calculate next day
                    tax_date_obj = datetime.strptime(tax_date, "%d/%m/%Y")
                    next_day = tax_date_obj + timedelta(days=1)
                    
                    # Create transaction record
                    record = {
                        'gateway': gateway,
                        'Order ID': f'TAX-{gateway}-{label.upper()}-{tax_date_obj.strftime("%d%m%Y")}',
                        'Amount': tax_value,
                        'tax_date': tax_date,
                        'Datetime': next_day,
                        'Hour': '00',  # Default to 12:00 AM for tax entries
                        'Minute': '00',
                        'Bank Reference': f'Interest Charge {label.title()} {tax_date_obj.strftime("%d/%m")}',
                        'Remarks': f'Interest Charge {label.upper()} {tax_date_obj.strftime("%d/%m")}',
                        'label': label,
                        'is_tax_record': True
                    }
                    
                    transaction_records.append(record)
                        
                print(f"✅ Processed {file_path}: Found {len(matches)} gateway tax entries")
            else:
                print(f"⚠️  No GRAND TOTAL section found in {file_path}")
                
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
    
    # Display results
    print("\n📊 Tax Transaction Records to Process:")
    print("=" * 80)
    
    total_tax = 0
    for record in transaction_records:
        print(f"Gateway: {record['gateway']:10} | Amount: Rs {record['Amount']:8.2f} | Date: {record['Datetime'].strftime('%d/%m/%Y')}")
        print(f"  Bank Ref: {record['Bank Reference']}")
        print(f"  Remarks:  {record['Remarks']}")
        print("-" * 80)
        total_tax += record['Amount']
    
    print(f"Total Tax Amount: Rs {total_tax:.2f}")
    
    # Group records by gateway
    gateway_records = {}
    for record in transaction_records:
        gateway = record['gateway']
        if gateway not in gateway_records:
            gateway_records[gateway] = []
        gateway_records[gateway].append(record)
    
    # Process each gateway
    for gateway, records in gateway_records.items():
        if gateway not in performed_gateways:
            gateway_setup_movement(gateway)
            performed_gateways.add(gateway)
        
        print(f"[DEBUG] Processing {len(records)} tax records for gateway '{gateway}'")
        for record in records:
            add_transaction_details(record)



# ===== Function call HERE =====
parse_and_execute("")  # Filename parameter not used in new implementation
time.sleep(2)  
driver.quit()

