import undetected_chromedriver as uc
import time
import json
import random
import re
import os
import yt_dlp
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import GUI logger (will fallback to print if GUI not running)
try:
    from panel import log_to_terminal
except ImportError:
    def log_to_terminal(text, color="#ffffff"):
        print(text)

# --- GLOBAL STATE ---
_driver = None
_config = None
_isScroll = False

def load_config():
    """Load configuration from data.config.json"""
    global _config
    try:
        with open('data.config.json', 'r', encoding='utf-8') as f:
            _config = json.load(f)
        log_to_terminal(f"Config loaded: @{_config.get('username', 'unknown')}, limit: {_config.get('limit', 'unlimited')}", "#00BFFF")
        return _config
    except Exception as e:
        log_to_terminal(f"Error loading config: {e}", "#FF4444")
        return None

def get_driver():
    """Get or create the Chrome driver instance."""
    global _driver
    return _driver

def get_hashtags(text):
    return re.findall(r"#\w+", text)

def get_video_url_from_tweet(tweet_url):
    """Extracts .mp4 URL using yt-dlp."""
    if not tweet_url: return None
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'get_url': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(tweet_url, download=False)
            return info.get('url', None)
    except:
        return None

def save_data(data, filename):
    """Helper to save data without overwriting previous progress"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    log_to_terminal(f"Saved {len(data)} tweets to {filename}", "#00FF04")

def check_rate_limit(driver):
    """
    Check if Twitter is showing rate limit / error page with Retry button.
    Returns True if rate limited, False otherwise.
    """
    try:
        # Look for the Retry button that appears on error
        retry_buttons = driver.find_elements(By.XPATH, '//button//span[text()="Retry"]')
        if retry_buttons:
            return True
        
        # Also check for "Something went wrong" text
        error_msgs = driver.find_elements(By.XPATH, '//*[contains(text(), "Something went wrong")]')
        if error_msgs:
            return True
    except:
        pass
    return False

def handle_rate_limit(driver, retry_count=0, max_retries=5):
    """
    Handle rate limit by waiting and clicking Retry.
    Returns True if recovered, False if max retries exceeded.
    """
    if retry_count >= max_retries:
        log_to_terminal(f"Max retries ({max_retries}) exceeded. Moving on...", "#FF4444")
        return False
    
    # Exponential backoff: 30s, 60s, 120s, 240s, 480s
    if _isScroll == True:
        wait_time = 1 * (2 ** retry_count) # Shorter wait during scrolls, its 10s,20s,40s,...
        # increase max retries during scrolls
        max_retries = 10
    else:
        wait_time = 30 * (2 ** retry_count) # Longer wait for initial rate limits, its 30s,60s,120s,...

    log_to_terminal(f"Rate limited! Waiting {wait_time}s before retry ({retry_count + 1}/{max_retries})...", "#FFAA00")
    
    time.sleep(wait_time)
    
    try:
        # Try to click the Retry button
        retry_buttons = driver.find_elements(By.XPATH, '//button//span[text()="Retry"]/ancestor::button')
        if retry_buttons:
            btn = retry_buttons[0]
            try:
                # Try JavaScript click first (more robust against interception)
                driver.execute_script("arguments[0].click();", btn)
                log_to_terminal("Clicked Retry button (JS).", "#00BFFF")
            except Exception:
                # Fallback to standard click
                btn.click()
                log_to_terminal("Clicked Retry button (Standard).", "#00BFFF")
            
            time.sleep(5)
            return True
        else:
            # If no button, just refresh the page
            driver.refresh()
            log_to_terminal("Refreshed page.", "#00BFFF")
            time.sleep(5)
            return True
    except Exception as e:
        log_to_terminal(f"Error during retry: {e}", "#FF4444")
        # Fallback: Refresh page if click failed
        try:
            driver.refresh()
            log_to_terminal("Refreshed page (fallback).", "#00BFFF")
            time.sleep(5)
            return True
        except:
            return False

def check_no_results(driver):
    """
    Check if Twitter is showing 'No results for' message.
    Returns True if no results found, False otherwise.
    """
    try:
        no_results = driver.find_elements(By.XPATH, '//span[contains(text(), "No results for")]')
        if no_results:
            return True
    except:
        pass
    return False

def human_type(element, text):
    """
    Types text into an element one character at a time with random delays
    to simulate human typing speed.
    """
    for char in text:
        element.send_keys(char)
        # Random delay between 50ms and 200ms per keystroke
        time.sleep(random.uniform(0.05, 0.2)) 

def login_to_x(driver, username, password):
    """
    Logs into X.com.
    Args:
        driver: The Selenium WebDriver instance.
        username: The login handle/email.
        password: The password.
    """
    wait = WebDriverWait(driver, 10)

    try:
        log_to_terminal(">> Starting human-like login flow...", "#00BFFF")

        # --- STEP 1: USERNAME ---
        # Locate by autocomplete attribute (more stable than obfuscated classes)
        username_field = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'input[autocomplete="username"]')
        ))
        
        # Mimic clicking the field to focus
        username_field.click()
        time.sleep(random.uniform(0.5, 1.2)) # Pause to "think"
        
        human_type(username_field, username)
        time.sleep(random.uniform(0.5, 1.0))

        # --- STEP 2: NEXT BUTTON ---
        # Locate by text content "Next" inside a span, inside a button
        # This bypasses the messy classes like 'r-sdzlij'
        next_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//span[text()='Next']/ancestor::button")
        ))
        next_button.click()
        
        # Wait for the slide animation/network request
        log_to_terminal("Waiting for password field...", "#888888")
        time.sleep(random.uniform(4.0, 6.0))

        # --- STEP 3: PASSWORD ---
        # Locate by name attribute
        password_field = wait.until(EC.visibility_of_element_located(
            (By.NAME, "password")
        ))
        
        password_field.click()
        time.sleep(random.uniform(0.5, 1.5))
        
        human_type(password_field, password)
        time.sleep(random.uniform(0.8, 1.5))

        # --- STEP 4: LOGIN BUTTON ---
        # Locate by data-testid (the most reliable hook provided by X devs)
        login_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[data-testid="LoginForm_Login_Button"]')
        ))
        login_button.click()

        log_to_terminal(">> Login submitted successfully.", "#00FF04")
        
        # Final wait to allow the dashboard to load
        time.sleep(random.uniform(3.0, 5.0))
        return True

    except Exception as e:
        log_to_terminal(f"!! Login failed: {e}", "#FF4444")
        return False

def run_automator():
    """
    Full automation: Load config, Open Browser, Auto-Login, Start Scraping.
    """
    global _driver, _config
    
    _config = load_config()
    if not _config:
        return

    my_username = _config.get('my_username')
    my_password = _config.get('my_password')

    if not my_username or not my_password:
        log_to_terminal("Error: Login credentials missing in config.", "#FF4444")
        return

    # Open Browser
    if not open_login_page(auto_mode=True):
        return

    # Auto Login
    if login_to_x(_driver, my_username, my_password):
        # Start Scraping
        start_scraping()
    else:
        log_to_terminal("Aborting scrape due to login failure.", "#FF4444")

def open_login_page(auto_mode=False):
    """Opens Chrome (undetected) and navigates to Twitter login page. Returns True on success."""
    global _driver
    try:
        log_to_terminal("Starting Undetected Chrome...", "#00BFFF")
        _driver = uc.Chrome(use_subprocess=True)

        log_to_terminal("Opening Twitter Login Page...", "#00BFFF")
        _driver.get("https://twitter.com/i/flow/login")
        
        log_to_terminal("Waiting for UI to load...", "#888888")
        time.sleep(5)

        if not auto_mode:
            log_to_terminal("", "#ffffff")
            log_to_terminal("=" * 50, "#FFFF00")
            log_to_terminal("[ACTION REQUIRED] Log in MANUALLY in the browser.", "#FFFF00")
            log_to_terminal("After logging in, click 'START SCRAPING' button.", "#FFFF00")
            log_to_terminal("=" * 50, "#FFFF00")
        
        return True
    except Exception as e:
        log_to_terminal(f"Error opening browser: {e}", "#FF4444")
        # Clean up if partially created
        try:
            if _driver:
                _driver.quit()
        except:
            pass
        _driver = None
        return False

def start_scraping():
    """Main scraping logic. Must be called after open_login_page() and manual login."""
    global _driver, _config, _isScroll
    
    if not _driver:
        log_to_terminal("Error: Browser not initialized. Click NEXT first.", "#FF4444")
        return
    
    if not _config:
        _config = load_config()
        if not _config:
            return
    
    TARGET_USER = _config.get('username', '')
    TOTAL_LIMIT = int(_config.get('limit', 100000000))
    BATCH_DAYS = 60
    
    if not TARGET_USER:
        log_to_terminal("Error: No username configured.", "#FF4444")
        return
    
    log_to_terminal(f"Starting scrape for @{TARGET_USER} (limit: {TOTAL_LIMIT})...", "#00FF04")
    
    # Load existing data if file exists (Resumable)
    filename = f"{TARGET_USER}_mega_scrape.json"
    scraped_data = []
    unique_ids = set()
    
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)
                for t in scraped_data:
                    if "tweet_url" in t and t["tweet_url"]:
                        unique_ids.add(t["tweet_url"])
            log_to_terminal(f"Resuming: Loaded {len(scraped_data)} existing tweets.", "#00BFFF")
        except:
            pass

    try:
        # DATE LOOP SETUP
        current_date = datetime.now()
        end_date = current_date - timedelta(days=BATCH_DAYS)
        
        total_collected = len(scraped_data)

        while total_collected < TOTAL_LIMIT:
            since_str = end_date.strftime("%Y-%m-%d")
            until_str = current_date.strftime("%Y-%m-%d")
            
            log_to_terminal(f"Batch: {since_str} to {until_str}", "#00BFFF")
            
            query = f"(from:{TARGET_USER}) until:{until_str} since:{since_str}"
            search_url = f"https://twitter.com/search?q={query}&src=typed_query&f=live"
            
            _driver.get(search_url)
            time.sleep(5)
            
            # Check for rate limit after loading page
            rate_limit_retries = 0
            _isScroll = False
            while check_rate_limit(_driver):
                if not handle_rate_limit(_driver, rate_limit_retries):
                    log_to_terminal("Skipping batch due to persistent rate limit.", "#FF4444")
                    break
                rate_limit_retries += 1
                # Reload the search page after retry
                _driver.get(search_url)
                time.sleep(5)
            
            # Check for "No results" - skip immediately if found
            if check_no_results(_driver):
                log_to_terminal(f"No tweets in range {since_str} to {until_str}. Skipping to next batch.", "#FFAA00")
                # Move dates and continue to next batch
                current_date = end_date
                end_date = current_date - timedelta(days=BATCH_DAYS)
                continue
            
            no_new_data_count = 0
            batch_collected = 0
            scroll_rate_limit_retries = 0
            
            while True:
                cards = _driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
                new_in_batch = False
                
                for card in cards:
                    try:
                        tweet_url = ""
                        try:
                            time_el = card.find_element(By.TAG_NAME, "time")
                            parent = time_el.find_element(By.XPATH, "./..")
                            tweet_url = parent.get_attribute("href")
                            tweet_date = time_el.get_attribute("datetime")
                        except:
                            continue

                        if tweet_url in unique_ids:
                            continue

                        try:
                            text = card.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
                        except:
                            text = ""
                            
                        image_urls = []
                        try:
                            imgs = card.find_elements(By.XPATH, './/div[@data-testid="tweetPhoto"]//img')
                            for img in imgs:
                                src = img.get_attribute("src")
                                if src: image_urls.append(src)
                        except:
                            pass
                            
                        has_video = False
                        try:
                            if card.find_elements(By.XPATH, './/div[@data-testid="videoComponent"]'):
                                has_video = True
                        except:
                            pass

                        real_video_url = None
                        if has_video:
                            real_video_url = get_video_url_from_tweet(tweet_url)

                        tweet_obj = {
                            "id": len(scraped_data) + 1,
                            "date": tweet_date,
                            "text": text,
                            "tweet_url": tweet_url,
                            "media_type": "video" if has_video else "image" if image_urls else "text",
                            "images": image_urls,
                            "video_url": real_video_url,
                            "hashtags": get_hashtags(text)
                        }
                        
                        scraped_data.append(tweet_obj)
                        unique_ids.add(tweet_url)
                        new_in_batch = True
                        batch_collected += 1
                        total_collected += 1
                        
                        log_to_terminal(f"   Collected: {tweet_date[:10]} | Total: {total_collected}", "#888888")
                        
                        # Buffer save: Save every 5 tweets to prevent data loss
                        if len(scraped_data) % 5 == 0:
                            save_data(scraped_data, filename)

                        # Check if limit reached
                        if total_collected >= TOTAL_LIMIT:
                            log_to_terminal(f"Limit of {TOTAL_LIMIT} tweets reached. Stopping scrape.", "#00FF04")
                            break

                    except Exception as e:
                        continue

                # Check if limit reached
                if total_collected >= TOTAL_LIMIT:
                    break  # Exit scroll loop

                _driver.execute_script(f"window.scrollBy(0, {random.randint(600, 1000)});")
                time.sleep(random.uniform(2, 4))
                
                # Check for rate limit during scrolling
                if check_rate_limit(_driver):
                    log_to_terminal("Rate limit detected during scroll. Handling...", "#FFAA00")
                    _isScroll = True
                    if handle_rate_limit(_driver, scroll_rate_limit_retries):
                        scroll_rate_limit_retries += 1
                        # Retry button clicked in handle_rate_limit, just continue to check for elements
                        continue
                    else:
                        break  # Exit scroll loop, move to next batch
                else:
                    scroll_rate_limit_retries = 0
                
                # Check if "No results" appeared (edge case)
                if check_no_results(_driver):
                    log_to_terminal("No more results in this batch.", "#FFAA00")
                    break
                
                if not new_in_batch:
                    no_new_data_count += 1
                    if no_new_data_count > 4:
                        log_to_terminal(f"Batch complete. Moving to next date range...", "#00BFFF")
                        break
                else:
                    no_new_data_count = 0
            
            save_data(scraped_data, filename)
            
            current_date = end_date
            end_date = current_date - timedelta(days=BATCH_DAYS)
            
            # Check if we've gone past 2006 (first year of tweets)
            if end_date.year < 2006:
                log_to_terminal("Completing scrape. All tweets collected.", "#00FF04")
                break
            
            if total_collected >= TOTAL_LIMIT:
                break

    except Exception as e:
        log_to_terminal(f"Critical Error: {e}", "#FF4444")
        save_data(scraped_data, filename)
        
    finally:
        if _driver:
            _driver.quit()
            _driver = None
        log_to_terminal(f"[COMPLETE] Saved {len(scraped_data)} tweets to {filename}", "#00FF04")

def cleanup():
    """Close browser if open."""
    global _driver
    if _driver:
        _driver.quit()
        _driver = None


# Only run standalone if executed directly
if __name__ == "__main__":
    # For standalone testing, create a simple config
    test_config = {"username": "elonmusk", "limit": "50"}
    with open('data.config.json', 'w') as f:
        json.dump(test_config, f)
    
    if open_login_page():
        input("Press ENTER after logging in...")
        start_scraping()