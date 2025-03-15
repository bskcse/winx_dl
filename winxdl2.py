import time
import atexit
import subprocess
from seleniumwire.undetected_chromedriver import Chrome, ChromeOptions

# Nadpisujemy klasę Chrome, aby zignorować metodę __del__
class CustomChrome(Chrome):
    def __del__(self):
        pass

driver = None  # Globalna referencja do przeglądarki

def extract_dynamic_links(url, quality):
    global driver

    # Konfiguracja opcji Chrome
    options = ChromeOptions()
    options.headless = False
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-insecure-localhost")

    seleniumwire_options = {
        'disable_encoding': True
    }

    try:
        if driver is None:  # Otwórz przeglądarkę tylko raz
            driver = CustomChrome(options=options, seleniumwire_options=seleniumwire_options)
        
        print(f"Otwieram stronę: {url}")
        driver.get(url)
        print("Czekam 10 sekund na załadowanie dynamicznej zawartości...")
        time.sleep(10)

        while True:
            playlist_links = {"playlist_sd": None, "playlist_dl": None, "playlist_pl": None}
            for request in driver.requests:
                if request.response:
                    request_url = request.url.strip()
                    if quality == "SD" and "playlist_sd" in request_url and request_url.endswith("index.html"):
                        playlist_links["playlist_sd"] = request_url
                    elif quality == "HD" and "playlist_dl" in request_url and request_url.endswith("index.html"):
                        playlist_links["playlist_dl"] = request_url
                    if "playlist_pl" in request_url and request_url.endswith("index.html"):
                        playlist_links["playlist_pl"] = request_url

            # Sprawdź, czy znaleziono odpowiednie linki
            if quality == "SD" and playlist_links["playlist_sd"] and playlist_links["playlist_pl"]:
                command_parts = [
                    f'N_m3u8DL-RE "{playlist_links["playlist_sd"]}" --save-name "video" --auto-select',
                    f'N_m3u8DL-RE "{playlist_links["playlist_pl"]}" --save-name "audio" --auto-select',
                    'mkvmerge -o final_video.mkv video.mp4 audio.m4a'
                ]
                full_command = " && ".join(command_parts)
                return full_command
            elif quality == "HD" and playlist_links["playlist_dl"] and playlist_links["playlist_pl"]:
                command_parts = [
                    f'N_m3u8DL-RE "{playlist_links["playlist_dl"]}" --save-name "video" --auto-select',
                    f'N_m3u8DL-RE "{playlist_links["playlist_pl"]}" --save-name "audio" --auto-select',
                    'mkvmerge -o final_video.mkv video.mp4 audio.m4a'
                ]
                full_command = " && ".join(command_parts)
                return full_command
            else:
                print("Nie znaleziono wymaganych linków. Zmień jakość lub ścieżkę dźwiękową ręcznie w przeglądarce.")
                input("Gdy skończysz, wciśnij Enter, aby ponownie przeszukać...")
                print("Przeszukuję ponownie...")
                time.sleep(5)  # Czekaj, aby użytkownik miał czas na wprowadzenie zmian

    except Exception as e:
        print(f"Błąd podczas przetwarzania: {e}")
        return None

def cleanup():
    global driver
    if driver is not None:
        try:
            driver.quit()
        except:
            pass
        finally:
            driver = None

atexit.register(cleanup)

if __name__ == "__main__":
    page_url = input("Podaj URL strony: ")
    quality = input("Wybierz jakość (SD/HD): ").upper()
    command = extract_dynamic_links(page_url, quality)
    
    if command:
        print("\nUruchamiam komendę w konsoli:")
        print("------------------------------")
        print(command + "\n")
        
        # Wykonaj komendę w konsoli Windows
        try:
            subprocess.run(command, shell=True, check=True)
            print("\nOperacja zakończona pomyślnie!")
        except subprocess.CalledProcessError as e:
            print(f"\nBłąd podczas wykonywania komendy: {e}")
    else:
        print("Nie udało się wygenerować komendy.")