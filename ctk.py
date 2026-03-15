import customtkinter
import datetime
import threading
import requests
import paramiko

VERSION = "1.1.1"
# Ustawienia wyglądu
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("dark-blue")

class App(customtkinter.CTk):
    def __init__(self, task: callable):
        super().__init__()
        # Konfiguracja głównego okna
        self.title("")
        self.geometry("500x400")
        
        # Deklaracje zmiennych i funckji
        self.task: callable = task
        self.driver = None

        # Konfiguracja siatki (grid)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Etykieta
        self.grid_rowconfigure(1, weight=1) # Pole tekstowe
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0) # Przycisk

        # Etykieta
        self.label = customtkinter.CTkLabel(self, text="Logi akcji:", font=("Arial", 14))
        self.label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")

        # Pole tekstowe (TextArea) na logi
        self.textbox = customtkinter.CTkTextbox(self)
        self.textbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Kolory tekstu
        self.textbox.tag_config("red", foreground="red")
        self.textbox.tag_config("green", foreground="green")
        self.textbox.tag_config("blue", foreground="blue")
        self.textbox.tag_config("yellow", foreground="yellow")
        
        self.textbox.insert("0.0", "Oczekiwanie na uruchomienie akcji...\n")  # Wstępna wiadomość
        self.textbox.configure(state="disabled") # Opcjonalnie: ustawiamy pole jako tylko do odczytu

        # Command wywołuje funkcję, która startuje wątek, a nie długą operację bezpośrednio
        self.button = customtkinter.CTkButton(self, text="Uruchom aplikację", command= lambda: self.start_action_thread(self.perform_task))
        self.button.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")

        self.button2 = customtkinter.CTkButton(self, text="Sprawdź aktualny token", command=lambda: self.log_message(self.check_token(self.input.get(), self.input1.get())))
        self.button2.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="nsew")

        self.button1 = customtkinter.CTkButton(self, text="Aktualizuj aplikację", command=lambda: self.start_action_thread(self.update))
        self.button1.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # Kolumna z kontrolkami dodatkowymi
        self.switch = customtkinter.CTkSwitch(self, text="Zmień kolor", command=self.color)
        self.switch.grid(row=1, column=1, padx=5, pady=(20,10), sticky="n")

        self.input = customtkinter.CTkEntry(self, placeholder_text="IP", textvariable=customtkinter.StringVar(value="192.168.100.12"))
        self.input.grid(row=3, column=1, padx=5, pady=(10,10),  sticky="n")
        self.input1 = customtkinter.CTkEntry(self, placeholder_text="Password", textvariable=customtkinter.StringVar(value="1111"))
        self.input1.grid(row=4, column=1, padx=5, pady=(0,10),  sticky="n")


    def log_message(self, message, color: str = "black"):
        """Dodaje wiadomość do pola tekstowego z timestampem."""
        self.textbox.configure(state="normal") 
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")

        self.textbox.insert("end", f"{timestamp} {message}\n", color)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def start_action_thread(self, task):
        """
        Funkcja uruchamiana przez przycisk. 
        Odpowiedzialna tylko za stworzenie i uruchomienie nowego wątku.
        """
        
        thread = threading.Thread(target=task, daemon=True)
        thread.start()

    def perform_task(self):
        """
        Ta funkcja działa w OSOBNYM wątku wykonawczym. 
        Może bezpiecznie używać time.sleep() bez blokowania wątku głównego (GUI).
        """
        self.button.configure(state="disabled")
        ip, password = self.input.get(), self.input1.get()
        
        self.task(ip, password)
        self.log_message("Akcja zakończona.")
        self.button.configure(state="normal")

    def color(self):
        """
        Funkcja zmieniająca tryb aplikacji między jasnym a ciemnym.
        """
        if customtkinter.get_appearance_mode() == "Light":
            customtkinter.set_appearance_mode("dark")
        else:
            customtkinter.set_appearance_mode("Light")

    def update(self):
        self.button1.configure(state="disabled")
        try:
            response = requests.get("http://192.168.100.147:5000", params={"version": VERSION}, stream=True)
            if response.ok:
                if response.headers.get("Content-Type") == "application/json":
                    self.log_message(response.json()["update"], "black")
                else:
                    with open(f"main{VERSION}.exe", "wb") as file: # Naprawić nazwę
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                file.write(chunk)
                    self.log_message("Pobrano aktualizację, zamknij program i uruchom nowy", "green")
            return
        
        except requests.exceptions.RequestException:
            self.log_message("Błąd pobierania aktualizacji, serwer jest wyłączony!", "red")
        finally:
            self.button1.configure(state="normal")

        # Naprawić i dodać zmiany pobranego pliku na main (poprzez bat). Naprawić funkcje, zrefaktoryzować kod.

    def check_token(self, ip, password):
        with paramiko.SSHClient() as client:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(ip, username='root', password=password)
                with client.open_sftp() as sftp:
                    with sftp.open("/etc/tuxbox/config/oscam.server", mode="r") as file:
                        content = file.read().decode("utf-8")
                        return f"Zawartość pliku oscam.server:\n{content}"
            except Exception as e:
                return f"Błąd podczas sprawdzania tokena: {e}"
    # def restart_device(self):
    #     ip, password = self.input.get(), self.input1.get()
    #     try:
    #         with paramiko.SSHClient() as client:
    #             client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #             client.connect(ip, username='root', password=password) 

    #             try:
    #                 stdin, stdout, stderr = client.exec_command("cd ../../sbin && ./reboot")
    #                 output = stdout.read().decode("utf-8")

    #                 self.log_message(output)
    #                 self.log_message("Urządzenie zostało zrestartowane.", "green")
    #             except paramiko.SSHException as e:
    #                 print(f"Błąd podczas restartu urządzenia: {e}")
    #                 self.log_message(f"Błąd podczas restartu urządzenia: {e}", "red")
    #     except Exception as e:
    #         print(f"Błąd podczas łączenia SSH: {e}")
    #         self.log_message(f"Błąd podczas łączenia SSH: {e}", "red")

