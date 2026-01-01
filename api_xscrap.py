import json
import time
import os
import random
import undetected_chromedriver as uc
from mega_parse import mega_parse
from json_to_pdf import generate_pdf
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Config:
    """Configuration for the Twitter Scraper"""
    # Browser Settings
    HEADLESS = False  # Set to True for production, False for debugging
    USER_DATA_DIR = "./chrome_profile"  # To persist login session
    
    # URLs
    LOGIN_URL = "https://x.com/i/flow/login"
    HOME_URL = "https://x.com/home"
    
    # Network Capture Settings
    # We need 'performance' logs to capture Network events via CDP
    LOGGING_PREFS = {'performance': 'ALL'}

def setup_driver(config=Config):
    """
    Initializes the Chrome driver with CDP (Chrome DevTools Protocol) enabled
    for network interception, using undetected-chromedriver to bypass bot detection.
    """
    options = uc.ChromeOptions()
    
    # Basic Chrome Options
    if config.HEADLESS:
        options.add_argument('--headless=new')
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    
    # Persist user profile
    abs_profile_path = os.path.abspath(config.USER_DATA_DIR)
    options.add_argument(f'--user-data-dir={abs_profile_path}')
    
    # Enable Performance Logging (CDP)
    options.set_capability('goog:loggingPrefs', config.LOGGING_PREFS)
    
    # Initialize Driver with undetected-chromedriver
    try:
        print("Initializing undetected_chromedriver...")
        driver = uc.Chrome(
            options=options,
            use_subprocess=True, # Helps with some environment issues
        )
        print(f"Browser launched successfully.")
        print(f"User Profile Path: {abs_profile_path}")
        return driver
    except Exception as e:
        print(f"Failed to initialize driver: {e}")
        raise e

def load_credentials():
    """Loads login credentials from data.config.json"""
    try:
        config_path = 'data.config.json'
        if not os.path.exists(config_path):
            print(f"Error: {config_path} not found.")
            return None
            
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def human_type(element, text):
    """
    Types text into an element one character at a time with random delays
    to simulate human typing speed.
    """
    for char in text:
        element.send_keys(char)
        # Random delay between 50ms and 200ms per keystroke
        time.sleep(random.uniform(0.05, 0.2))

def login(driver, username, password):
    """
    Logs into X.com using the provided credentials.
    Adapted from twitter_login_scrape.py
    """
    wait = WebDriverWait(driver, 15)
    
    print(f"Attempting login for user: {username}")
    driver.get(Config.LOGIN_URL)
    
    try:
        # Check if already logged in (redirected to home)
        time.sleep(3)
        if "home" in driver.current_url:
            print("Already logged in.")
            return True

        # --- STEP 1: USERNAME ---
        print("Waiting for username field...")
        # Locate by autocomplete attribute (more stable than obfuscated classes)
        username_field = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'input[autocomplete="username"]')
        ))
        
        # Mimic clicking the field to focus
        username_field.click()
        time.sleep(random.uniform(0.5, 1.2))
        
        human_type(username_field, username)
        time.sleep(random.uniform(0.5, 1.0))

        # --- STEP 2: NEXT BUTTON ---
        print("Clicking Next...")
        # Locate by text content "Next" inside a span, inside a button
        next_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//span[text()='Next']/ancestor::button")
        ))
        next_button.click()
        
        # Wait for the slide animation/network request
        time.sleep(random.uniform(2.0, 4.0))

        # --- STEP 3: PASSWORD ---
        print("Waiting for password field...")
        # Locate by name attribute
        password_field = wait.until(EC.visibility_of_element_located(
            (By.NAME, "password")
        ))
        
        password_field.click()
        time.sleep(random.uniform(0.5, 1.5))
        
        human_type(password_field, password)
        time.sleep(random.uniform(0.8, 1.5))

        # --- STEP 4: LOGIN BUTTON ---
        print("Clicking Login...")
        # Locate by data-testid
        login_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[data-testid="LoginForm_Login_Button"]')
        ))
        login_button.click()

        print("Login submitted. Waiting for home page...")
        
        # Final wait to allow the dashboard to load
        # We wait for the URL to change to home or for a home-specific element
        try:
            wait.until(EC.url_contains("home"))
            print("Login successful! Redirected to Home.")
            return True
        except:
            # Sometimes it doesn't redirect immediately or asks for verification
            # For now, we assume if no error, we are good, or check for an element
            if driver.current_url == "https://x.com/home":
                return True
            print("Warning: Did not detect redirect to /home. Check browser.")
            return False

    except Exception as e:
        print(f"Login failed: {e}")
        return False

def extract_tweet_data(tweet_result, thread_id=None):
    """Extracts relevant fields from the tweet_result object"""
    if not tweet_result:
        return None
        
    # Handle TweetWithVisibilityResults wrapper
    if tweet_result.get('__typename') == 'TweetWithVisibilityResults':
        tweet_result = tweet_result.get('tweet', {})
        
    legacy = tweet_result.get('legacy')
    if not legacy:
        return None
        
    core = tweet_result.get('core', {}).get('user_results', {}).get('result', {})
    # Handle UserWithVisibilityResults if necessary
    if core.get('__typename') == 'UserWithVisibilityResults':
        core = core.get('user', {})
        
    user_legacy = core.get('legacy', {})
    
    # Fallback for missing user info in legacy (seen in some API responses)
    user_core = core.get('core', {})
    user_avatar = core.get('avatar', {})
    
    name = user_legacy.get('name') or user_core.get('name')
    screen_name = user_legacy.get('screen_name') or user_core.get('screen_name')
    profile_image_url = user_legacy.get('profile_image_url_https') or user_avatar.get('image_url')
    
    # Extract Media (Images/Videos)
    media_urls = []
    extended_entities = legacy.get('extended_entities', {})
    if 'media' in extended_entities:
        for media in extended_entities['media']:
            if media.get('type') == 'photo':
                media_urls.append(media.get('media_url_https'))
            elif media.get('type') == 'video':
                # Get highest bitrate variant
                variants = media.get('video_info', {}).get('variants', [])
                best_variant = max(
                    [v for v in variants if v.get('content_type') == 'video/mp4'], 
                    key=lambda x: x.get('bitrate', 0), 
                    default=None
                )
                if best_variant:
                    media_urls.append(best_variant.get('url'))

    return {
        'id': legacy.get('id_str'),
        'thread_id': thread_id, # Link to the main thread
        'created_at': legacy.get('created_at'),
        'full_text': legacy.get('full_text'),
        'user': {
            'name': name,
            'screen_name': screen_name,
            'profile_image_url': profile_image_url
        },
        'metrics': {
            'reply_count': legacy.get('reply_count'),
            'retweet_count': legacy.get('retweet_count'),
            'favorite_count': legacy.get('favorite_count'),
            'quote_count': legacy.get('quote_count'),
            'view_count': tweet_result.get('views', {}).get('count')
        },
        'media': media_urls,
        'lang': legacy.get('lang'),
        'is_thread': bool(thread_id)
    }

def parse_response(response_json):
    """Parses the full UserTweets API response"""
    parsed_tweets = []
    incomplete_threads = []
    
    try:
        # Debugging: Check path existence
        data = response_json.get('data', {})
        if not data:
            return [], []
            
        user = data.get('user', {})
        result = user.get('result', {})
        
        timeline_obj = result.get('timeline', {})
        if not timeline_obj:
             timeline_obj = result.get('timeline_v2', {})
        
        timeline = timeline_obj.get('timeline', {})
        
        if not timeline:
            return [], []

        instructions = timeline.get('instructions', [])
        
        for instruction in instructions:
            inst_type = instruction.get('type')
            
            # Handle Pinned Tweet
            if inst_type == 'TimelinePinEntry':
                entry = instruction.get('entry', {})
                content = entry.get('content', {})
                tweet_res = content.get('itemContent', {}).get('tweet_results', {}).get('result', {})
                tweet_data = extract_tweet_data(tweet_res)
                if tweet_data:
                    tweet_data['is_pinned'] = True
                    parsed_tweets.append(tweet_data)

            # Handle Main Timeline
            elif inst_type == 'TimelineAddEntries':
                entries = instruction.get('entries', [])
                
                for entry in entries:
                    content = entry.get('content', {})
                    entryType = content.get('entryType')
                    
                    # 1. Single Tweet
                    if entryType == 'TimelineTimelineItem':
                        tweet_res = content.get('itemContent', {}).get('tweet_results', {}).get('result', {})
                        tweet_data = extract_tweet_data(tweet_res)
                        if tweet_data:
                            parsed_tweets.append(tweet_data)
                            
                    # 2. Thread / Conversation Module
                    elif entryType == 'TimelineTimelineModule':
                        items = content.get('items', [])
                        
                        # Get Thread Metadata to check for completeness
                        metadata = content.get('metadata', {}).get('conversationMetadata', {})
                        all_tweet_ids = metadata.get('allTweetIds', [])
                        
                        # Determine Thread ID (First tweet in the list)
                        thread_id = None
                        if items:
                            first_item = items[0]
                            first_res = first_item.get('item', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {})
                            # Handle wrapper
                            if first_res.get('__typename') == 'TweetWithVisibilityResults':
                                first_res = first_res.get('tweet', {})
                            thread_id = first_res.get('legacy', {}).get('id_str')

                        # Check if incomplete
                        # If we have fewer items than total IDs, we need to fetch the rest
                        if len(items) < len(all_tweet_ids) and thread_id:
                            print(f"Found incomplete thread {thread_id}: {len(items)}/{len(all_tweet_ids)} tweets.")
                            incomplete_threads.append(thread_id)

                        for item in items:
                            item_content = item.get('item', {}).get('itemContent', {})
                            tweet_res = item_content.get('tweet_results', {}).get('result', {})
                            # Pass thread_id to link them
                            tweet_data = extract_tweet_data(tweet_res, thread_id=thread_id)
                            if tweet_data:
                                parsed_tweets.append(tweet_data)
                                
    except Exception as e:
        print(f"Error parsing response: {e}")
        
    return parsed_tweets, incomplete_threads

def parse_tweet_detail(response_json):
    """Parses the TweetDetail API response for full threads"""
    parsed_tweets = []
    try:
        data = response_json.get('data', {})
        instructions = data.get('threaded_conversation_with_injections_v2', {}).get('instructions', [])
        
        for instruction in instructions:
            if instruction.get('type') == 'TimelineAddEntries':
                entries = instruction.get('entries', [])
                for entry in entries:
                    content = entry.get('content', {})
                    entryType = content.get('entryType')
                    
                    if entryType == 'TimelineTimelineItem':
                        tweet_res = content.get('itemContent', {}).get('tweet_results', {}).get('result', {})
                        tweet_data = extract_tweet_data(tweet_res)
                        if tweet_data:
                            parsed_tweets.append(tweet_data)
                    
                    elif entryType == 'TimelineTimelineModule':
                        items = content.get('items', [])
                        for item in items:
                            item_content = item.get('item', {}).get('itemContent', {})
                            tweet_res = item_content.get('tweet_results', {}).get('result', {})
                            tweet_data = extract_tweet_data(tweet_res)
                            if tweet_data:
                                parsed_tweets.append(tweet_data)
    except Exception as e:
        print(f"Error parsing detail response: {e}")
    return parsed_tweets

def fetch_incomplete_threads(driver, thread_ids):
    """
    Fetches full data for incomplete threads.
    Uses the main window to avoid 'invalid session id' issues with tab management in undetected_chromedriver.
    """
    if not thread_ids:
        return

    print(f"--- Phase 4.5: Fetching {len(thread_ids)} incomplete threads ---")
    
    for tid in thread_ids:
        try:
            print(f"Processing thread {tid}...")
            
            # Navigate to tweet detail directly in the current tab
            # This is more stable than opening/closing tabs with uc
            url = f"https://x.com/i/status/{tid}"
            driver.get(url)
            time.sleep(5) # Wait for load
            
            # Scan logs for TweetDetail
            logs = driver.get_log("performance")
            found = False
            
            for entry in logs:
                try:
                    log_obj = json.loads(entry["message"])
                    message = log_obj.get("message", {})
                    method = message.get("method")
                    
                    if method == "Network.responseReceived":
                        params = message.get("params", {})
                        response = params.get("response", {})
                        url = response.get("url", "")
                        request_id = params.get("requestId")
                        
                        if "TweetDetail" in url and "variables" in url:
                            print(f"Found TweetDetail API for {tid}")
                            try:
                                body_data = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                                body = body_data['body']
                                data = json.loads(body)
                                
                                # Parse
                                full_thread_tweets = parse_tweet_detail(data)
                                
                                # Mark them all with the thread_id
                                for t in full_thread_tweets:
                                    t['thread_id'] = tid
                                    t['is_thread'] = True
                                
                                # Save
                                filename = f"thread_{tid}_full.json"
                                with open(filename, "w", encoding="utf-8") as f:
                                    json.dump(full_thread_tweets, f, indent=4, ensure_ascii=False)
                                print(f"Saved full thread to {filename}")
                                found = True
                                break
                            except Exception as e:
                                print(f"Error getting body: {e}")
                except:
                    continue
            
            if not found:
                print(f"Warning: Could not capture TweetDetail for {tid}")
                
            time.sleep(2)
            
        except Exception as e:
            print(f"Error processing thread {tid}: {e}")

def scroll_page(driver):
    """Scrolls down the page to trigger new content loading."""
    # Scroll down by a random amount
    scroll_amount = random.randint(500, 800)
    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
    time.sleep(random.uniform(2.0, 4.0)) # Wait for network requests

def scrape_profile(driver, username, limit=50):
    """
    Navigates to user profile, scrolls, and intercepts multiple UserTweets GraphQL responses.
    """
    profile_url = f"https://x.com/{username}"
    print(f"Navigating to profile: {profile_url}")
    driver.get(profile_url)
    
    # Wait for initial load
    print("Waiting for page load (5s)...")
    time.sleep(5)
    
    processed_urls = set() # The "security_log" to track fetched APIs
    batch_count = 0
    total_tweets = 0
    
    # Queue for incomplete threads
    incomplete_threads_queue = set()
    
    # Safety break for no-progress (since we removed max_scrolls)
    no_new_data_scrolls = 0
    max_no_data_scrolls = 15
    
    while total_tweets < limit:
        print(f"Scanning network logs (Collected: {total_tweets}/{limit})...")
        
        # Get current logs (this consumes them, so we only get new ones since last call)
        logs = driver.get_log("performance")
        found_new_batch = False
        
        for entry in logs:
            try:
                log_obj = json.loads(entry["message"])
                message = log_obj.get("message", {})
                method = message.get("method")
                
                if method == "Network.responseReceived":
                    params = message.get("params", {})
                    response = params.get("response", {})
                    url = response.get("url", "")
                    request_id = params.get("requestId")
                    
                    # Check if it's the UserTweets API
                    if "UserTweets" in url and "variables" in url:
                        # Check security log
                        if url not in processed_urls:
                            print(f"Found new UserTweets API: {url[:100]}...")
                            
                            try:
                                # Fetch the body using CDP
                                body_data = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                                body = body_data['body']
                                
                                # Parse and Save
                                data = json.loads(body)
                                
                                # Save Raw Data (Debug)
                                raw_filename = f"{batch_count + 1}_raw_api.json"
                                with open(raw_filename, "w", encoding="utf-8") as f:
                                    json.dump(data, f, indent=4)
                                print(f"Saved raw response to {raw_filename}")
                                
                                # Parse
                                new_tweets, incomplete_ids = parse_response(data)
                                
                                if new_tweets:
                                    # Check limit and truncate if necessary
                                    remaining = limit - total_tweets
                                    if len(new_tweets) > remaining:
                                        new_tweets = new_tweets[:remaining]
                                        # Filter incomplete_ids to only those in the truncated list
                                        kept_ids = set(t['id'] for t in new_tweets)
                                        incomplete_ids = [tid for tid in incomplete_ids if tid in kept_ids]
                                    
                                    count = len(new_tweets)
                                    print(f"Parsed {count} tweets from this batch.")
                                    
                                    # Save Individual Batch Data (RAM Optimization)
                                    batch_filename = f"{batch_count + 1}_api_parsed.json"
                                    with open(batch_filename, "w", encoding="utf-8") as f:
                                        json.dump(new_tweets, f, indent=4, ensure_ascii=False)
                                    print(f"Saved batch to {batch_filename}")
                                    
                                    total_tweets += count
                                    found_new_batch = True
                                else:
                                    print(f"Warning: No tweets parsed from batch {batch_count + 1}")
                                
                                # Add incomplete threads to queue
                                if incomplete_ids:
                                    for tid in incomplete_ids:
                                        incomplete_threads_queue.add(tid)

                                # Add to security log
                                processed_urls.add(url)
                                batch_count += 1
                                
                                if total_tweets >= limit:
                                    break
                                    
                            except Exception as e:
                                print(f"Failed to get body for {request_id}: {e}")
                        else:
                            # Already processed this URL
                            pass
            except Exception:
                continue
        
        if total_tweets >= limit:
            print(f"Tweet limit of {limit} reached.")
            break
            
        if not found_new_batch:
            no_new_data_scrolls += 1
            if no_new_data_scrolls >= max_no_data_scrolls:
                print("No new data found after multiple scrolls. Stopping.")
                break
        else:
            no_new_data_scrolls = 0
            
        # Scroll to trigger more content
        print("Scrolling...")
        scroll_page(driver)
        
    if total_tweets == 0:
        print("No tweets collected.")
    else:
        print(f"Successfully captured {total_tweets} tweets in {batch_count} batches.")
        
    # Phase 4.5: Process Incomplete Threads
    if incomplete_threads_queue:
        fetch_incomplete_threads(driver, list(incomplete_threads_queue))
    else:
        print("No incomplete threads found.")

# Global logger function for GUI integration
_logger = None

def set_logger(logger_func):
    """Set a custom logger function for GUI output."""
    global _logger
    _logger = logger_func

def log(message, color="#ffffff"):
    """Log a message to GUI or console."""
    if _logger:
        _logger(message, color)
    else:
        print(message)

def run_automator():
    """
    Main entry point for the scraper.
    Called by the GUI (panel.py) or can be run standalone.
    Returns the path to the generated JSON file, or None on failure.
    """
    driver = None
    json_file = None
    
    try:
        log("--- Phase 3: Profile Scraping ---", "#00FF04")
        
        # 1. Load Credentials
        config_data = load_credentials()
        if not config_data:
            log("Error: Could not load configuration.", "#FF4444")
            return None
            
        my_username = config_data.get('my_username')
        my_password = config_data.get('my_password')
        target_user = config_data.get('username', 'dayendtrader')
        limit = int(config_data.get('limit', 1000000000))
        
        log(f"Target: @{target_user}, Limit: {limit}", "#888888")

        # 2. Setup Driver
        log("Setting up browser...", "#00BFFF")
        driver = setup_driver()
        
        # 3. Login
        log("Logging in...", "#00BFFF")
        if not login(driver, my_username, my_password):
            log("Login failed.", "#FF4444")
            return None
            
        # 4. Scrape Profile
        log(f"Scraping @{target_user}...", "#00BFFF")
        scrape_profile(driver, target_user, limit)
        
        # 5. Close Browser BEFORE post-processing
        log("Closing browser...", "#888888")
        driver.quit()
        driver = None  # Mark as closed
        
        # 6. Mega Parse
        log("Running Mega Parse...", "#00BFFF")
        mega_parse(target_user)
        
        json_file = f"{target_user}_mega_scrape.json"
        if os.path.exists(json_file):
            log(f"Data saved to {json_file}", "#00FF04")
            return json_file
        else:
            log(f"Warning: {json_file} not found.", "#FFAA00")
            return None
                
    except Exception as e:
        log(f"Error during execution: {e}", "#FF4444")
        return None
    finally:
        # Ensure browser is closed even on error
        if driver:
            try:
                driver.quit()
            except:
                pass


if __name__ == "__main__":
    # Standalone execution (without GUI)
    json_path = run_automator()
    
    if json_path:
        print(f"Generating PDF from {json_path}...")
        generate_pdf(json_path)
    else:
        print("Scraping failed or no data collected.")
