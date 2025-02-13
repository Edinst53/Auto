from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import requests
import random
import string
import time
import json
import sys
from colorama import init, Fore, Style, Back
import os
import threading
import itertools

class FacebookCreator:
    def __init__(self):
        init()  # Initialize colorama
        self.max_attempts = 10
        self.successful_accounts = []
        self.failed_attempts = 0
        chrome_options = webdriver.ChromeOptions()
        # Add random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
        # Add additional options to avoid detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        # Add more stealth options
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.temp_mail_api = "https://www.1secmail.com/api/v1/"
        self.signup_url = "https://www.facebook.com/r.php"
        self.login_check = 20  # Maximum attempts to check for verification email
        self.email_retries = 3  # Number of retries for email
        
        # Add lists of names
        self.first_names_male = ['James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Charles']
        self.first_names_female = ['Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica', 'Sarah', 'Karen']
        self.last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        self.checkpoint_urls = [
            "checkpoint",
            "identity",
            "verification",
            "confirm",
            "security",
            "help"
        ]
        self.expected_url = "https://www.facebook.com/r.php"
        self.valid_urls = [
            "facebook.com/r.php",
            "facebook.com/reg",
            "facebook.com/registration"
        ]
        self.checkpoint_patterns = [
            "checkpoint",
            "identity",
            "confirm",
            "verification",
            "help",
            "disabled",
            "security",
            "?next="
        ]
        self.loading_event = threading.Event()
        self.checkpoint_detected = False
    
    def generate_password(self, length=12):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))
    
    def get_temp_email(self):
        for _ in range(self.email_retries):
            try:
                print("Fetching temporary email...")
                response = requests.get(f"{self.temp_mail_api}?action=genRandomMailbox&count=1")
                response.raise_for_status()
                data = response.json()
                if data and '@' in data[0]:  # Verify email format
                    email = data[0]
                    # Verify email format
                    if self.validate_email(email):
                        print(f"Valid temporary email fetched: {email}")
                        return email
                print("Invalid email received, retrying...")
                time.sleep(2)
            except Exception as e:
                print(f"Error fetching email: {str(e)}")
                time.sleep(2)
        return None

    def validate_email(self, email):
        import re
        # Basic email validation pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def get_email_messages(self, email):
        try:
            username, domain = email.split('@')
            response = requests.get(
                f"{self.temp_mail_api}?action=getMessages&login={username}&domain={domain}"
            )
            return response.json()
        except Exception as e:
            print(f"Error getting messages: {str(e)}")
            return []

    def get_verification_code(self, email):
        print("Waiting for verification email...")
        attempts = 0
        while attempts < self.login_check:
            messages = self.get_email_messages(email)
            for message in messages:
                if "facebook" in message.get('from', '').lower():
                    # Get message content
                    try:
                        username, domain = email.split('@')
                        response = requests.get(
                            f"{self.temp_mail_api}?action=readMessage&login={username}&domain={domain}&id={message['id']}"
                        )
                        content = response.json()
                        # Extract code from email content
                        if 'body' in content:
                            # Look for patterns like "FB-12345" or numbers
                            import re
                            matches = re.findall(r'FB-?\d+|(?<!\d)\d{5,6}(?!\d)', content['body'])
                            if matches:
                                code = matches[0].replace('FB-', '')
                                print(f"Verification code found: {code}")
                                return code
                    except Exception as e:
                        print(f"Error reading message: {str(e)}")
            
            attempts += 1
            print(f"Waiting for email... Attempt {attempts}/{self.login_check}")
            time.sleep(10)
        
        print("No verification code found")
        return None

    def enter_verification_code(self, code):
        try:
            # Wait for code input field
            code_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "code")) or
                EC.presence_of_element_located((By.NAME, "confirm")) or
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'][placeholder*='code']"))
            )
            code_input.send_keys(code)
            
            # Find and click continue/submit button
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            
            print("Verification code submitted")
            time.sleep(5)
            return True
        except Exception as e:
            print(f"Error entering verification code: {str(e)}")
            return False
    
    def generate_random_date(self):
        day = random.randint(1, 28)
        month = random.randint(1, 12)
        year = random.randint(1990, 2000)
        return day, month, year
    
    def random_delay(self, min_delay=1, max_delay=3):
        """Add random delay between actions"""
        time.sleep(random.uniform(min_delay, max_delay))

    def human_like_movement(self):
        """Simulate human-like mouse movements"""
        try:
            action = ActionChains(self.driver)
            # Random mouse movements
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 700)
                y = random.randint(100, 500)
                action.move_by_offset(x, y)
                action.perform()
                self.random_delay(0.5, 1.5)
        except Exception as e:
            print(f"Mouse movement error: {str(e)}")

    def monitor_url_changes(self):
        """Enhanced URL monitoring"""
        try:
            current_url = self.driver.current_url.lower()
            print(f"Current URL: {current_url}")
            
            # Ignore common Facebook redirects
            ignored_patterns = [
                "gettingstarted",
                "welcome",
                "home.php",
                "privacy_mutation_token",
                "dialog"
            ]
            
            if any(pattern in current_url for pattern in ignored_patterns):
                print("Safe redirect detected, continuing...")
                return True
                
            # Check if we're on a valid registration URL
            is_valid_url = any(url in current_url for url in self.valid_urls)
            
            if not is_valid_url and not any(pattern in current_url for pattern in ignored_patterns):
                if any(pattern in current_url for pattern in self.checkpoint_patterns):
                    self.print_box("Checkpoint detected! Starting new attempt...", "warning")
                    self.checkpoint_detected = True
                    return False
                print(f"Warning: Not on registration page: {current_url}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Error monitoring URL: {str(e)}")
            return False

    def check_for_checkpoint(self):
        """Improved checkpoint detection"""
        try:
            # Only proceed with checkpoint checks if not on registration page
            if not self.monitor_url_changes():
                if self.checkpoint_detected:
                    self.save_error_screenshot()
                    return False
                return True

            # Check page source for checkpoint indicators
            page_source = self.driver.page_source.lower()
            checkpoint_texts = [
                "checkpoint required",
                "security check",
                "confirm your identity",
                "verify your account",
                "something went wrong",
                "we need more information",
                "suspicious activity",
                "please wait",
                "try again later"
            ]
            
            for text in checkpoint_texts:
                if text in page_source:
                    self.print_box(f"Checkpoint detected: {text}", "warning")
                    self.checkpoint_detected = True
                    self.save_error_screenshot()
                    return False

            return True

        except Exception as e:
            self.print_status(f"Error in checkpoint detection: {str(e)}", "error")
            return False

    def save_error_screenshot(self):
        """Save screenshot when error occurs"""
        try:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            self.driver.save_screenshot(f"checkpoint_error_{timestamp}.png")
            print("Error screenshot saved")
        except Exception as e:
            print(f"Failed to save screenshot: {str(e)}")

    def fill_form(self, first_name, last_name, email, password, day, month, year, gender):
        try:
            print("Filling the form...")
            # ...existing code...
            self.random_delay(2, 4)
            self.human_like_movement()
            
            # Fill first name
            first_name_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "firstname"))
            )
            first_name_element.clear()
            first_name_element.send_keys(first_name)
            self.random_delay(0.5, 1)
            
            # Fill last name
            last_name_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "lastname"))
            )
            last_name_element.clear()
            last_name_element.send_keys(last_name)
            self.random_delay(0.5, 1)
            
            # Fill email and confirmation
            email_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "reg_email__"))
            )
            email_element.clear()
            email_element.send_keys(email)
            self.random_delay(0.5, 1)
            try:
                conf_email_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "reg_email_confirmation__"))
                )
                conf_email_element.clear()
                conf_email_element.send_keys(email)
            except Exception:
                pass
            
            # Fill password
            password_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "reg_passwd__"))
            )
            password_element.clear()
            password_element.send_keys(password)
            self.random_delay(0.5, 1)
            
            # Select birthday using Select elements
            from selenium.webdriver.support.ui import Select
            day_select = Select(WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "day"))
            ))
            day_select.select_by_value(str(day))
            month_select = Select(self.driver.find_element(By.ID, "month"))
            month_select.select_by_value(str(month))
            year_select = Select(self.driver.find_element(By.ID, "year"))
            year_select.select_by_value(str(year))
            self.random_delay(0.5, 1)
            
            # Select gender radio button
            if gender == "1":  # Female
                gender_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@name='sex' and @value='1']"))
                )
            else:  # Male
                gender_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@name='sex' and @value='2']"))
                )
            gender_button.click()
            self.random_delay(0.5, 1)
            
            # Submit the form
            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "websubmit"))
            )
            submit_button.click()
            
            print("Form submitted, waiting for processing...")
            time.sleep(30)
            self.human_like_movement()
            self.random_delay()
            self.check_for_checkpoint()
            # ...existing code...
        except Exception as e:
            print(f"Error in form filling: {str(e)}")
            self.save_error_screenshot()
            print("Detailed error information:", str(e.__class__))
            raise e
    
    def save_account_info(self, account_info):
        try:
            with open("facebook_accounts.txt", "a") as f:
                f.write(json.dumps(account_info) + "\n")
            print("Account information saved.")
        except Exception as e:
            print(f"Error saving account information: {str(e)}")
    
    def verify_account_creation(self, email, password):
        try:
            print("Verifying account creation...")
            self.driver.get("https://www.facebook.com/login")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, "email"))
            ).send_keys(email)
            self.driver.find_element(By.NAME, "pass").send_keys(password)
            self.driver.find_element(By.NAME, "login").click()
            
            time.sleep(10)  # Wait for login process
            
            if "login_attempt" in self.driver.current_url:
                print("Account verification failed. Login attempt detected.")
                return False
            else:
                print("Account verified successfully!")
                return True
        except Exception as e:
            print(f"Error verifying account: {str(e)}")
            return False
    
    def create_account(self, first_name=None, last_name=None, gender=None):
        try:
            self.checkpoint_detected = False
            self.start_loading("Creating new account")
            self.print_status("Starting account creation process...", "info")
            # Clear cookies before starting
            self.clear_cookies()
            
            print("Navigating to Facebook signup page...")
            self.driver.get(self.signup_url)
            
            # Add cloudflare bypass
            self.bypass_cloudflare()
            
            # Initial checkpoint check
            if not self.check_for_checkpoint():
                self.stop_loading()
                self.print_box("Checkpoint detected! Retrying with new account...", "warning")
                self.driver.delete_all_cookies()
                return None
            
            if "r.php" not in self.driver.current_url:
                self.stop_loading()
                self.print_box("Checkpoint detected!", "warning")
                return None
            
            if not gender:
                gender = random.choice(['1', '2'])  # 1 for female, 2 for male
                
            if not first_name:
                if gender == '1':  # female
                    first_name = random.choice(self.first_names_female)
                else:  # male
                    first_name = random.choice(self.first_names_male)
                    
            if not last_name:
                last_name = random.choice(self.last_names)
            
            email = self.get_temp_email()
            if not email:
                print("Failed to get temporary email. Aborting account creation.")
                return None
            
            password = self.generate_password()
            day, month, year = self.generate_random_date()
            
            self.fill_form(first_name, last_name, email, password, day, month, year, gender)
            
            # Wait for potential verification request
            time.sleep(10)
            
            # Check for verification code
            code = self.get_verification_code(email)
            if code:
                if not self.enter_verification_code(code):
                    print("Failed to enter verification code")
                    return None
            
            account_info = {
                "email": email,
                "password": password,
                "name": f"{first_name} {last_name}",
                "birthday": f"{day}/{month}/{year}",
                "gender": "female" if gender == '1' else "male"
            }
            
            self.save_account_info(account_info)
                
            time.sleep(10)  # Wait for registration process
            
            # Verify account creation
            if self.verify_account_creation(email, password):
                self.stop_loading()
                self.print_box("Account created successfully!", "success")
                return account_info
            else:
                self.stop_loading()
                self.print_box("Account creation failed", "error")
                return None
            
        except Exception as e:
            self.stop_loading()
            self.print_box("Process interrupted", "warning")
            self.print_status(f"Error creating account: {str(e)}", "error")
            self.save_error_screenshot()
            return None
        
    def close(self):
        self.driver.quit()

    def bypass_cloudflare(self):
        """Add delays and movements to bypass Cloudflare"""
        try:
            self.random_delay(3, 5)
            self.human_like_movement()
            # Scroll down and up
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            self.random_delay(1, 2)
            self.driver.execute_script("window.scrollTo(0, 0);")
        except Exception as e:
            print(f"Error in cloudflare bypass: {str(e)}")

    def clear_cookies(self):
        """Clear cookies and cache"""
        try:
            self.driver.delete_all_cookies()
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            print("Cookies and cache cleared")
        except Exception as e:
            print(f"Error clearing cookies: {str(e)}")

    def clear_terminal(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_status(self, message, status="info"):
        """Print colored status messages"""
        colors = {
            "success": Fore.GREEN,
            "error": Fore.RED,
            "info": Fore.CYAN,
            "warning": Fore.YELLOW
        }
        print(f"{colors.get(status, Fore.WHITE)}{message}{Style.RESET_ALL}")

    def print_progress(self):
        """Print current progress"""
        self.clear_terminal()
        print("=" * 50)
        self.print_status(f"Account Creation Progress", "info")
        print(f"Attempts: {self.failed_attempts + len(self.successful_accounts)}/{self.max_attempts}")
        print(f"Successful: {len(self.successful_accounts)}")
        print(f"Failed: {self.failed_attempts}")
        print("=" * 50)

    def run_creation_loop(self):
        """Main account creation loop"""
        self.clear_terminal()
        self.print_box("Facebook Account Creator", "info")
        
        while (self.failed_attempts + len(self.successful_accounts)) < self.max_attempts:
            try:
                print("\n" + "=" * 50)
                self.print_box(f"Attempt {self.failed_attempts + len(self.successful_accounts) + 1}/{self.max_attempts}", "info")
                
                account = self.create_account()
                
                if account:
                    self.successful_accounts.append(account)
                    self.print_box("✓ Success!", "success")
                    print(f"{Fore.GREEN}Email: {account['email']}")
                    print(f"Password: {account['password']}")
                    print(f"Name: {account['name']}{Style.RESET_ALL}")
                else:
                    self.failed_attempts += 1
                    if self.checkpoint_detected:
                        self.print_box("⚠ Checkpoint detected - Starting new attempt...", "warning")
                    else:
                        self.print_box("✗ Failed - Retrying...", "error")
                
                time.sleep(3)
                self.clear_terminal()
                
                # Show current stats
                print(f"\n{Fore.CYAN}Progress:{Style.RESET_ALL}")
                print(f"{'▰' * len(self.successful_accounts)}{'▱' * (self.max_attempts - len(self.successful_accounts))}")
                self.print_box(f"Success: {len(self.successful_accounts)} | Failed: {self.failed_attempts}", "info")
                
            except Exception as e:
                self.failed_attempts += 1
                self.print_status(f"Error: {str(e)}", "error")
                continue

        # Final results
        self.clear_terminal()
        self.print_box("Final Results", "info")
        self.print_box(f"Successful: {len(self.successful_accounts)}", "success")
        self.print_box(f"Failed: {self.failed_attempts}", "error")
        
        if self.successful_accounts:
            print("\n" + "=" * 50)
            self.print_box("Created Accounts", "success")
            for account in self.successful_accounts:
                print(f"\n{Fore.CYAN}► Account Details:{Style.RESET_ALL}")
                print(f"  Name: {account['name']}")
                print(f"  Email: {account['email']}")
                print(f"  Password: {account['password']}")
                print(f"  Birthday: {account['birthday']}")
                print(f"  Gender: {account['gender']}")

    def loading_animation(self, text="Processing"):
        """Show loading animation"""
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        for char in itertools.cycle(chars):
            if self.loading_event.is_set():
                break
            print(f'\r{Fore.CYAN}{text} {char}', end='')
            time.sleep(0.1)
        print(f'\r{" " * 50}\r', end='')  # Clear the line
        
    def start_loading(self, text="Processing"):
        """Start loading animation in separate thread"""
        self.loading_event.clear()
        self.loading_thread = threading.Thread(target=self.loading_animation, args=(text,))
        self.loading_thread.start()
        
    def stop_loading(self):
        """Stop loading animation"""
        self.loading_event.set()
        self.loading_thread.join()
        
    def print_box(self, text, style="info"):
        """Print text in a box"""
        colors = {
            "success": Fore.GREEN,
            "error": Fore.RED,
            "info": Fore.CYAN,
            "warning": Fore.YELLOW
        }
        color = colors.get(style, Fore.WHITE)
        width = len(text) + 4
        print(f"{color}╔{'═' * width}╗")
        print(f"║  {text}  ║")
        print(f"╚{'═' * width}╝{Style.RESET_ALL}")

if __name__ == "__main__":
    creator = FacebookCreator()
    try:
        creator.run_creation_loop()
    finally:
        creator.close()
