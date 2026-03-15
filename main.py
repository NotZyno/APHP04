import sys
import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_recaptcha_solver import RecaptchaSolver # Ta biblioteka wymaga ffmpeg
from pythonping import ping
import time
import pyautogui
import random
import paramiko
import ctk

#a
# Dodać switcha do visibility
# naprawić nazwy funkcji

OSCAM_CONF_PATH = "/etc/tuxbox/config/oscam.server"
REBOOT_CMD = "cd /etc/init.d/ && /etc/init.d/softcam restart"
TEMP_MAIL_URL = "https://temp-mail.org/en/10minutemail"
TARGET_SITE_URL = "https://cccam.eu/"

def run_selenium(ip, password,) -> None:
    global driver
    driver = None
    token = ""
    
    try:
        if not check_ssh(ip):
            print("Urządzenie jest wyłączone.")
            app.log_message("Urządzenie jest wyłączone.", "green")
            return
        

        # Opcje konfiguracji przeglądarki
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--window-position=0,0")
        
        # Inicjalizacji przeglądarki i solvera
        driver = uc.Chrome(options=options, use_subprocess=True, keep_alive=True, version_main=146)
        solver = RecaptchaSolver(driver)
        
        # install_adblock(driver) # Deprecated - niepotrzebne, strona nie posiada reklam

        mail = setup_mail(driver)

        send_request_and_solve_captcha(driver, solver, mail)

        token = get_token_from_email(driver)
    except Exception as e:
        app.log_message(f"Wystąpił błąd podczas trwania selenium: {e}", "red")

    try:
        if not token:
            app.log_message("Nie udało się pobrać tokena z maila.", "red")
            return
        app.log_message("Zamykam przeglądarkę i uruchamiam SSH", "green")
        setup_ssh(token, ip, password)
    except Exception as e:
        print(f"Wystąpił błąd podczas trwania programu: {e}")
        app.log_message(f"Wystąpił błąd podczas trwania programu: {e}", "red")
    finally:
        if driver:
            driver.quit()

def check_ssh(ip):
    """
    Funkcja sprawdzająca, czy urządzenie jest włączone
    """
    try:
        response = ping(ip, count=2, timeout=2)
        if response.success():
            return True
        return False
    except Exception as e:
        print(f"Błąd podczas pingowania: {e}")
        return False
        
def setup_ssh(token, ip, password):
    PATH = "/etc/tuxbox/config/oscam.server"
    
    try:
        with paramiko.SSHClient() as client:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, username='root', password=password) 

            with client.open_sftp() as sftp:
                with sftp.open(PATH, mode="w") as file:
                    file.write(token if token else "brak tokena")
                    file.flush()

                client.exec_command("sync")
            print("Plik oscam.server został zaktualizowany.")
            app.log_message("Plik oscam.server został zaktualizowany.", "green")

            time.sleep(2)
            stdin, stdout, stderr = client.exec_command("cd /etc/init.d/ && /etc/init.d/softcam restart")
            output = stdout.read().decode("utf-8")
            app.log_message(output.strip('\n'))
    except (Exception, paramiko.SSHException) as e:
        app.log_message(f"Błąd podczas aktualizacji pliku oscam.server: {e}", "red")

def setup_mail(driver: uc.Chrome):
    driver.get(TEMP_MAIL_URL)
    time.sleep(10)

    WebDriverWait(driver, 14.523534673).until(EC.presence_of_element_located((By.ID, "mail")))
    element_value = driver.find_element(By.ID, "mail").get_attribute("value")
    return element_value
    
def install_adblock(driver: uc.Chrome):
    driver.get("https://chromewebstore.google.com/detail/adblock-%E2%80%94-block-ads-acros/gighmmpiobklfepjocnamgkkbiglidom?hl=pl")
    driver.find_element(By.CLASS_NAME, "UywwFc-LgbsSe").click()
    pyautogui.moveTo(988, 303)
    time.sleep(2)
    pyautogui.click()
    time.sleep(15)
    driver.switch_to.window(driver.window_handles[0])

def send_request_and_solve_captcha(driver: uc.Chrome, solver: RecaptchaSolver, email: str):
    driver.get(TARGET_SITE_URL)
    try:
        accept_button = WebDriverWait(driver, 10.426457434).until(EC.visibility_of_element_located((By.XPATH, "//a[@class='cc-btn cc-allow']")))
        accept_button.click()
        app.log_message("Zaakceptowano pliki cookie.")
    except Exception:
        app.log_message("Baner cookies nie pojawił się lub wystąpił inny problem z nim.", "yellow")

    try:
        WebDriverWait(driver, 15.543524467).until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(email)
        captcha_iframe = driver.find_element(By.XPATH, "//iframe[@title='reCAPTCHA']")

        driver.execute_script("arguments[0].scrollIntoView(true);", captcha_iframe)
    except Exception as e:
        app.log_message(f"Wystąpił błąd podczas próby przewinięcia do CAPTCHA: {e}", "yellow")

    while(True):
        """Pętla, która sprawdza, czy CAPTCHA jest rozwiązana, jeśli jest przechodzi dalej"""
        try:
            driver.switch_to.default_content()

            driver.switch_to.frame(captcha_iframe)
            checkbox = driver.find_element(By.CLASS_NAME, "recaptcha-checkbox")
            is_solved = checkbox.get_attribute("aria-checked") == "true"
            driver.switch_to.default_content()

            if is_solved:
                break 
            # Jeśli nie jest rozwiązana, dopiero wtedy wywołaj solver
            solver.click_recaptcha_v2(captcha_iframe)
            # ---------------------------------------

        except Exception as e:
            driver.switch_to.default_content()
            app.log_message("Błąd CAPTCHA. Ponawiam próbę za 5 sekund...", "yellow")
            time.sleep(5)
            continue
        break

    driver.switch_to.default_content() # zmiana contentu drivera na domyślny

    accept_button = WebDriverWait(driver, 10.4245534).until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']")))
    accept_button.click()
    time.sleep(0.746466543)

def get_token_from_email(driver: uc.Chrome):
    token = ""
    driver.get(TEMP_MAIL_URL)
    driver.refresh()

    time.sleep(6.45435363)
    WebDriverWait(driver, 15.4234663464324).until(EC.presence_of_element_located((By.CLASS_NAME, "inboxSenderEllipsis")))

    i = 6
    while True:
        try:
            email = driver.find_elements(By.CLASS_NAME, "inboxSenderEllipsis")[i]
            time.sleep(random.random()%3+0.449)
            email.click()
        except Exception as e:
            i -= 2
            if i < 0: break
            continue
            
    try:
        time.sleep(1.429)
        driver.execute_script("window.scrollTo(0, 1600);")
    except Exception as e:
        print(f"Wystąpił błąd podczas próby pobrania tokena z maila: {e}")
        app.log_message(f"Wystąpił błąd podczas próby pobrania tokena z maila: {e}", "red")
        return ""

    try:
        text = driver.find_elements(By.XPATH, "//p[contains(., '[reader]')]")

        token = text[0].text + "\n" + text[1].text
        
        print("***************** Token *****************")
        print(text[0].text)
        print("\n")
        print(text[1].text)
        
        print("*****************************************")

        app.log_message("Pomyślnie skopiowano token z maila.", "green")
    except Exception as e:
        token = ""
    return token
# pip install pyautogui paramiko selenium undetected-chromedriver selenium-recaptcha-solver pyperclip, pobrać ffmpeg
def main():
    global app
    global driver
    driver = None

    app = ctk.App(run_selenium)
    app.protocol("WM_DELETE_WINDOW", lambda: (driver.quit() if driver else None, app.destroy(), sys.exit()))
    app.mainloop()

main()
