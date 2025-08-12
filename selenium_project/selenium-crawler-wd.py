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
from datetime import datetime
from collections import defaultdict




options = Options()
# options.add_argument('--headless')  # Uncomment if you want headless mode

service = Service(GeckoDriverManager().install())
driver = webdriver.Firefox(service=service, options=options)
driver.maximize_window()


driver.get("https://v3-bo.backofficeltaj.com/en-us")

wait = WebDriverWait(driver, 40)
merchant_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Merchant Code']")))
merchant_input.send_keys("lucky")

wait = WebDriverWait(driver, 40)
merchant_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Username']")))
merchant_input.send_keys("test_8899")

wait = WebDriverWait(driver, 40)
merchant_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Password']")))
merchant_input.send_keys("Mcd6033035!")





def get_captcha_number(driver, timeout=40):
    # Wait for the outer div with all digits to appear
    wait = WebDriverWait(driver, timeout)
    outer_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-v-450e3340].tracking-normal")))
    
    # Now safely collect child <span> elements
    digits = outer_div.find_elements(By.CSS_SELECTOR, "span[data-v-450e3340]")
    
    captcha_text = ''.join([d.text for d in digits])
    print(f"[DEBUG] Found {len(digits)} spans, captcha: {captcha_text}")
    
    return captcha_text




# Wait for CAPTCHA input field to appear

wait = WebDriverWait(driver, 40)
captcha_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Captcha Code']")))
captcha_code = get_captcha_number(driver)
captcha_input.send_keys(captcha_code)

print("\033[92mExtracted CAPTCHA:", captcha_code, "\033[0m")
captcha_input.send_keys(Keys.ENTER)

# ======== Entered Main Page ========

# Wait for sidebar to appear

wait = WebDriverWait(driver, 40)
menu_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='Finance Management']]")))


WebDriverWait(driver, 20).until(
    EC.invisibility_of_element_located((By.CLASS_NAME, "ajaxLoader"))
)
print("\033[94m[INFO] ajaxLoader complete\033[0m")
time.sleep(2)


menu_link.click()

# Step 2: Wait for submenu item to be visible and clickable
submenu_item = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[span[@class='bullet-point'] and text()='Withdraw']")))
submenu_item.click()



# ======== Entered 2.1 Deposit =======


# Wait for panel loading
WebDriverWait(driver, 20).until(
    EC.invisibility_of_element_located((By.CLASS_NAME, "box box-info"))
)
print("[INFO] Panel load complete")


time.sleep(2)

# Wait for ajax loader loading
WebDriverWait(driver, 20).until(
    EC.invisibility_of_element_located((By.CLASS_NAME, "ajaxLoader"))
)
print("\033[94m[INFO] ajaxLoader complete\033[0m")

time.sleep(2)

# Wait for the Status dropdown to be present and click it to open
status_dropdown = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//div[@class='label' and text()='Status']/following-sibling::div//div[contains(@class,'o-input-wrapper')]"))
)
status_dropdown.click()

# Wait for dropdown to be open and select "Approved"
time.sleep(1)  # Give dropdown time to fully open
approved_option = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Approved')]"))
)
approved_option.click()
print("[INFO] Clicked on Approved option")


# Select date section

# select_date = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-type="today"]')))
# select_date.click()

# Manual date selection pause
print("⏸️ Paused for manual date selection.")
input("👉 Please select the date manually in the browser, then press ENTER here to continue...")
print("✅ Date selected, continuing...")

# Wait for 'No Record' Icon dissapeared

WebDriverWait(driver, 20).until(
    EC.invisibility_of_element_located((By.CLASS_NAME, "box box-info no-record-holder"))
)
print("\033[94m[INFO] Table load complete\033[0m")


# ======= Print Logic Here =======

def extract_transaction_data(driver, wait_timeout=20):
    """Waits for transaction table rows to appear and extracts structured data."""
    
    # Wait until at least one row exists
    WebDriverWait(driver, wait_timeout).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "table tbody tr")) > 0
    )

    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    print(f"[INFO] Total rows found: {len(rows)}")

    gateway_groups = defaultdict(list)

    for idx in range(len(rows)):
        try:
            # Re-find rows to avoid stale element reference
            current_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            if idx >= len(current_rows):
                print(f"[WARNING] Row {idx + 1} no longer exists. Skipping.")
                continue
                
            row = current_rows[idx]
            cols = row.find_elements(By.TAG_NAME, 'td')
            
            
            if len(cols) < 5:  # Reduce minimum column requirement
                print(f"[WARNING] Row {idx + 1} has only {len(cols)} columns. Skipping.")
                continue
            
            # Filter out summary rows
            first_col_text = cols[0].text.strip() if len(cols) > 0 else ""
            if "Page Summary" in first_col_text or "Total Summary" in first_col_text:
                print(f"[INFO] Skipping summary row: '{first_col_text}'")
                continue

            try:
                # Parse amount with soft error handling
                amount_text = cols[12].text.strip().replace("Rs", "").replace(",", "").strip()
                try:
                    amount = float(amount_text) if amount_text else 0.0
                except ValueError:
                    print(f"[WARNING] Invalid amount '{amount_text}' in row {idx + 1}, setting to 0.0")
                    amount = 0.0
                
                # Parse tax fee with soft error handling
                tax_text = cols[13].text.strip().replace(",", "")
                try:
                    tax_fee = float(tax_text) if tax_text else 0.0
                except ValueError:
                    print(f"[WARNING] Invalid tax fee '{tax_text}' in row {idx + 1}, setting to 0.0")
                    tax_fee = 0.0
                
                record = {
                    "Gateway": cols[24].text.strip() if len(cols) > 21 else "Unknown",
                    "Order ID": cols[1].text.strip(),
                    "Phone Number": cols[8].text.strip(),
                    "Amount": amount,
                    "Time": cols[18].text.strip() if len(cols) > 20 else "",
                    "Tax Fee": tax_fee
                }
                gateway_groups[record["Gateway"]].append(record)

            except Exception as e:
                print(f"[ERROR] Failed to parse data in row {idx + 1}: {e}")
                continue
                
        except Exception as e:
            print(f"[ERROR] Stale element or other error in row {idx + 1}: {e}")
            continue

    return gateway_groups



def print_grouped_results(gateway_groups):

    grand_total = 0
    grand_tax_total = 0

    with open("selenium_project/wd-selenium-transaction_history.txt", "w", encoding="utf-8") as f:
        for gateway, records in gateway_groups.items():
            
            total_amount = sum(record["Amount"] if isinstance(record["Amount"], (int, float)) else float(record["Amount"].replace(",", "")) for record in records)
            grand_total += total_amount 

            total_tax_amount = sum(float(record["Tax Fee"]) for record in records)
            grand_tax_total += total_tax_amount

            header = f"\n==== {gateway} ({len(records)} record{'s' if len(records) != 1 else ''}) | Total Amount: Rs {total_amount:,.2f} | Total Fee: Rs {total_tax_amount:.2f} ====\n"
            print(f"\033[92m{header}\033[0m")
            f.write(header)

            # Sort records by time (latest first) with error handling
            def safe_parse_time(record):
                try:
                    if record["Time"] and record["Time"].strip():
                        return datetime.strptime(record["Time"], "%Y-%m-%d %H:%M:%S")
                    else:
                        return datetime.min  # Put records with no time at the end
                except ValueError:
                    print(f"[WARNING] Invalid time format: '{record['Time']}'")
                    return datetime.min

            sorted_records = sorted(records, key=safe_parse_time, reverse=True)

            for i, record in enumerate(sorted_records, 1):
                # print(f"[DEBUG] Record {i} in {gateway}: {record}")  

                entry = (
                    f"\nRecord #{i}\n"
                    f"Order ID: {record['Order ID']}\n"
                    f"Phone Number: {record['Phone Number']}\n"
                    f"Amount: {record['Amount']:,.2f}\n"
                    f"Time: {record['Time']}\n"
                )
                print(f"\033[94m{entry}\033[0m")
                f.write(entry)

            footer = f"\n>> Total Amount for {gateway}: Rs {total_amount:,.2f}\n"
            print(f"\033[93m{footer}\033[0m")
            f.write(footer)

        total_records = sum(len(records) for records in gateway_groups.values())
        f.flush()
        os.fsync(f.fileno())

        # ✅ Only once at the end
        grand_footer = f"\n==== GRAND TOTAL for All Gateways: Rs {grand_total:,.2f} | Total Records: {total_records} ====\n\n"
        print(f"\033[95m{grand_footer}\033[0m")
        f.write(grand_footer)
        
        # Print individual gateway tax amounts
        for gateway, records in gateway_groups.items():
            total_tax_amount = round(sum(float(record["Tax Fee"]) for record in records), 2)
            # Extract date from the first record's time (assuming all records are from same date)
            try:
                if records[0]["Time"] and records[0]["Time"].strip():
                    transaction_date = datetime.strptime(records[0]["Time"], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
                else:
                    transaction_date = "Unknown"
            except (ValueError, IndexError):
                transaction_date = "Unknown"
            gateway_tax_line = f"(wd) pg {gateway} {transaction_date} | Total Fee: Rs {total_tax_amount:.2f}\n"
            print(f"\033[95m{gateway_tax_line}\033[0m")
            f.write(gateway_tax_line)



def click_next_page(driver, wait_timeout=10):
    try:
        next_button = WebDriverWait(driver, wait_timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ml-3 button"))
        )
        next_button.click()
        time.sleep(2)
        print("[INFO] Clicked on the Next button.")
        return True
    except Exception as e:
        print(f"[WARNING] Could not click Next button: {e}")
        return False



gateway_groups = defaultdict(list)  # Global collector
seen_order_ids = set()  # Track seen Order IDs to prevent duplicates

def run_full_transaction_extraction(driver):
    page_counter = 1
    duplicate_count = 0
    while True:
        print(f"\033[92m[INFO] Scraping page {page_counter}...\033[0m")

        # Extract data from current page
        current_page_data = extract_transaction_data(driver)

        # Merge current data into the global group, checking for duplicates
        for gateway, records in current_page_data.items():
            for record in records:
                order_id = record["Order ID"]
                if order_id not in seen_order_ids:
                    gateway_groups[gateway].append(record)
                    seen_order_ids.add(order_id)
                else:
                    duplicate_count += 1
                    print(f"\033[93m[WARNING] Duplicate Order ID '{order_id}' found on page {page_counter}. Skipping.\033[0m")

        # Try to go to next page
        has_next = click_next_page(driver)
        if not has_next:
            print("[INFO] No more pages found. Finishing extraction.")
            break

        page_counter += 1
        time.sleep(1)  

    if duplicate_count > 0:
        print(f"\033[93m[INFO] Total duplicates skipped: {duplicate_count}\033[0m")
    
    print_grouped_results(gateway_groups)
    
run_full_transaction_extraction(driver)

time.sleep(5)  
driver.quit()