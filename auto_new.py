from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import random
import string
import re

# Fungsi untuk mengambil temporary email dari mail.tm dan membuat akun agar bisa menerima email
def get_temp_email():
    mail_tm_password = "Password123!"  # password untuk akun mail.tm
    try:
        # Ambil domain yang tersedia dari mail.tm
        domains_resp = requests.get("https://api.mail.tm/domains")
        domains_resp.raise_for_status()
        domains_data = domains_resp.json()
        domain = domains_data['hydra:member'][0]['domain']
        
        # Buat username acak sepanjang 10 karakter
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"{username}@{domain}"
        
        # Daftarkan akun pada mail.tm agar email dapat menerima pesan
        account_data = {
            "address": email,
            "password": mail_tm_password
        }
        create_resp = requests.post("https://api.mail.tm/accounts", json=account_data)
        if create_resp.status_code not in [200, 201]:
            print("Peringatan: Pembuatan akun mail.tm mungkin gagal, menggunakan email:", email)
        return email, mail_tm_password
    except Exception as e:
        print(f"Error fetching temporary email: {e}")
        return "temp@example.com", "temp"

# Fungsi untuk menghasilkan data pengguna secara acak
def random_user_data():
    first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Hank", "Ivy", "Jack"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia", "Rodriguez", "Wilson"]

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    
    # Tanggal lahir valid (1-28 untuk hari agar tidak terjadi invalid date)
    bday = random.randint(1, 28)
    bmonth = random.randint(1, 12)
    byear = random.randint(1970, 2000)
    
    # Pilih jenis kelamin acak: "1" untuk Female, "2" untuk Male
    gender_value = random.choice(["1", "2"])
    
    # Generate password acak untuk Facebook dengan panjang 10 karakter
    password_length = 10
    password_characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(password_characters) for _ in range(password_length))

    return {
        "first_name": first_name,
        "last_name": last_name,
        "bday": bday,
        "bmonth": bmonth,
        "byear": byear,
        "gender_value": gender_value,
        "password": password
    }

# Fungsi untuk mengisi formulir signup Facebook
def fill_signup_form(driver, first_name, last_name, email, password, bday, bmonth, byear, gender_value):
    driver.get("https://www.facebook.com/r.php")
    wait = WebDriverWait(driver, 10)
    
    # Isi nama depan
    fname = wait.until(EC.presence_of_element_located((By.NAME, "firstname")))
    fname.clear()
    fname.send_keys(first_name)
    
    # Isi nama belakang
    lname = wait.until(EC.presence_of_element_located((By.NAME, "lastname")))
    lname.clear()
    lname.send_keys(last_name)
    
    # Isi email dan konfirmasi email (jika ada)
    email_field = wait.until(EC.presence_of_element_located((By.NAME, "reg_email__")))
    email_field.clear()
    email_field.send_keys(email)
    try:
        conf_email = wait.until(EC.presence_of_element_located((By.NAME, "reg_email_confirmation__")))
        conf_email.clear()
        conf_email.send_keys(email)
    except Exception:
        pass
    
    # Isi password
    pwd = wait.until(EC.presence_of_element_located((By.NAME, "reg_passwd__")))
    pwd.clear()
    pwd.send_keys(password)
    
    # Pilih tanggal lahir
    day_sel = Select(wait.until(EC.presence_of_element_located((By.ID, "day"))))
    day_sel.select_by_value(str(bday))
    month_sel = Select(wait.until(EC.presence_of_element_located((By.ID, "month"))))
    month_sel.select_by_value(str(bmonth))
    year_sel = Select(wait.until(EC.presence_of_element_located((By.ID, "year"))))
    year_sel.select_by_value(str(byear))
    
    # Pilih jenis kelamin
    gender_radio = wait.until(EC.element_to_be_clickable((By.XPATH, f"//input[@name='sex' and @value='{gender_value}']")))
    gender_radio.click()
    
    # Submit formulir
    submit_btn = wait.until(EC.element_to_be_clickable((By.NAME, "websubmit")))
    submit_btn.click()

# Fungsi untuk mendeteksi status setelah pendaftaran (checkpoint, error, atau sukses)
def check_account_status(driver):
    time.sleep(5)
    current_url = driver.current_url.lower()
    page_source = driver.page_source.lower()
    
    if "checkpoint" in current_url or "checkpoint" in page_source:
        return "checkpoint"
    elif "error" in page_source:
        return "error"
    else:
        return "success"

# Fungsi untuk mendapatkan token dari mail.tm agar dapat mengakses inbox
def get_mailtm_token(email, mail_tm_password):
    try:
        token_resp = requests.post("https://api.mail.tm/token", json={"address": email, "password": mail_tm_password})
        token_resp.raise_for_status()
        token_data = token_resp.json()
        return token_data["token"]
    except Exception as e:
        print(f"Error mendapatkan token mail.tm: {e}")
        return None

# Fungsi untuk mengambil kode verifikasi dari inbox mail.tm dengan polling selama beberapa detik
def get_verification_code(token, subject_keyword="facebook"):
    headers = {"Authorization": f"Bearer {token}"}
    timeout = 60  # total waktu tunggu (detik)
    poll_interval = 5
    total_wait = 0
    while total_wait < timeout:
        try:
            messages_resp = requests.get("https://api.mail.tm/messages", headers=headers)
            messages_resp.raise_for_status()
            messages_data = messages_resp.json()
            for message in messages_data.get("hydra:member", []):
                if subject_keyword.lower() in message.get("subject", "").lower():
                    # Ambil detail pesan untuk mendapatkan isi email
                    message_detail_resp = requests.get(f"https://api.mail.tm/messages/{message['id']}", headers=headers)
                    message_detail_resp.raise_for_status()
                    message_detail = message_detail_resp.json()
                    # Cari kode verifikasi berupa 6 digit dalam teks email
                    match = re.search(r'\b(\d{6})\b', message_detail.get("text", ""))
                    if match:
                        return match.group(1)
        except Exception as e:
            print(f"Error mendapatkan pesan: {e}")
        time.sleep(poll_interval)
        total_wait += poll_interval
    return None

def main():
    driver = webdriver.Chrome()
    try:
        # Dapatkan temporary email dan password untuk mail.tm
        temp_email, mail_tm_password = get_temp_email()
        user_data = random_user_data()
        
        print(f"Menggunakan temporary email: {temp_email}")
        print("Data pengguna acak:", user_data)
        
        fill_signup_form(driver, 
                         first_name=user_data["first_name"], 
                         last_name=user_data["last_name"], 
                         email=temp_email, 
                         password=user_data["password"], 
                         bday=user_data["bday"], 
                         bmonth=user_data["bmonth"], 
                         byear=user_data["byear"], 
                         gender_value=user_data["gender_value"])
        
        # Tunggu beberapa saat setelah submit pendaftaran
        time.sleep(10)
        status = check_account_status(driver)
        if status == "checkpoint":
            print("Akun terkena checkpoint!")
        elif status == "error":
            print("Gagal membuat akun!")
        else:
            print("Berhasil membuat akun!")
            # Dapatkan token untuk mengakses inbox mail.tm
            token = get_mailtm_token(temp_email, mail_tm_password)
            if token:
                print("Memeriksa inbox untuk kode verifikasi...")
                code = get_verification_code(token)
                if code:
                    print(f"Kode verifikasi ditemukan: {code}")
                    # -- Di sini Anda dapat menambahkan logika untuk mengisi form verifikasi di Facebook, jika diperlukan --
                else:
                    print("Kode verifikasi tidak ditemukan dalam batas waktu.")
            else:
                print("Tidak dapat mengambil token dari mail.tm.")
            # Simpan data akun ke file akun.txt
            with open("akun.txt", "a") as f:
                f.write(f"{user_data['first_name']} {user_data['last_name']} - {temp_email}:{user_data['password']}\n")
    finally: 
        driver.quit()

if __name__ == "__main__":
    main()
