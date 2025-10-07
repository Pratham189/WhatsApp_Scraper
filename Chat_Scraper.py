import os
import re
import requests
from time import sleep
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from prettytable import PrettyTable
from dotenv import load_dotenv


def set_up_driver():
    load_dotenv()
    DRIVER_PATH = os.getenv('DRIVER_PATH')
    CHROME_PROFILE = os.getenv('CHROME_PROFILE')
    options = webdriver.ChromeOptions()
    if CHROME_PROFILE:
        options.add_argument(f"user-data-dir={CHROME_PROFILE}")
    service = Service(DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_script_timeout(90)
    return driver


def Check_User_Log_In(driver, wait_time):
    try:
        WebDriverWait(driver, wait_time).until(
            expected_conditions.presence_of_element_located((By.ID, 'pane-side'))
        )
        return True
    except TimeoutException:
        return False


def whatsapp_load(driver):
    print("Running Whatsapp...", end="\r")
    driver.get('https://web.whatsapp.com/')

    logged_in, wait_time = False, 20
    while not logged_in:
        logged_in = Check_User_Log_In(driver, wait_time)
        if not logged_in:
            print(f"Error: WhatsApp failed to load within {wait_time} seconds. Make sure you are logged in and try again.")
            err_response = input("Proceed  Yes(Y) or No(N) ?")
            if err_response.strip().lower() in {'y', 'yes'}:
                continue
            elif err_response.strip().lower() in {'n', 'no'}:
                return False
    print("Success! WhatsApp finished loading and is ready.")
    return True


def download_media(url, save_path):
    try:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            return True
    except Exception as e:
        print("Download failed:", e)
    return False


def get_chat_messages(driver, chat_name, limit=30):
    """
    Extracts messages (text, images, videos) from the currently opened chat
    and downloads media to disk.
    """
    messages = []
    chat_body = WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='conversation-panel-body']"))
    )

    # Scroll up to load more messages
    for _ in range(2):
        driver.execute_script("arguments[0].scrollTop = 0;", chat_body)
        sleep(2)

    rows = chat_body.find_elements(By.CSS_SELECTOR, "div[role='row']")[-limit:]

    # Create folder for this chat
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', chat_name)
    folder = os.path.join("downloads", safe_name)
    os.makedirs(folder, exist_ok=True)

    for idx, row in enumerate(rows):
        try:
            text = ""
            media = []

            try:
                text = row.find_element(By.CSS_SELECTOR, "span[dir='ltr']").text
            except:
                pass

            # Extract images
            imgs = row.find_elements(By.CSS_SELECTOR, "img[src]")
            for i, img in enumerate(imgs):
                src = img.get_attribute("src")
                filename = os.path.join(folder, f"image_{idx}_{i}.jpg")
                if download_media(src, filename):
                    media.append({"type": "image", "path": filename})

            # Extract videos
            vids = row.find_elements(By.CSS_SELECTOR, "video source[src]")
            for i, vid in enumerate(vids):
                src = vid.get_attribute("src")
                filename = os.path.join(folder, f"video_{idx}_{i}.mp4")
                if download_media(src, filename):
                    media.append({"type": "video", "path": filename})

            if text or media:
                messages.append({
                    "text": text,
                    "media": media
                })
        except Exception:
            continue

    return messages


def get_chats(driver):
    print("Loading your chats...", end="\r")
    chats = []
    try:
        chat_pane = WebDriverWait(driver, 20).until(
            expected_conditions.presence_of_element_located((By.ID, "pane-side"))
        )
        chat_rows = chat_pane.find_elements(By.CSS_SELECTOR, "div[role='row']")

        for row in chat_rows[:3]:  # limit to first 3 for demo
            try:
                name = row.find_element(By.CSS_SELECTOR, "span[title]").get_attribute("title")
            except:
                name = "Unknown"

            row.click()
            sleep(2)

            messages = get_chat_messages(driver, name, limit=20)

            chats.append({
                "name": name,
                "messages": messages
            })

        print("✅ Success! Chats with messages/media have been loaded.")

    except Exception as e:
        print("⚠️ Error while scraping chats:", e)

    return chats


def print_msg(chats):
    t = PrettyTable()
    t.field_names = ["#", "Chat Name", "Sample Msg/Media"]

    for key in t.align.keys():
        t.align[key] = "l"
    t._max_width = {
        "#": 3,
        "Chat Name": 20,
        "Sample Msg/Media": 60
    }

    for i, chat in enumerate(chats, start=1):
        sample = ""
        if chat["messages"]:
            first = chat["messages"][0]
            if first["text"]:
                sample = first["text"]
            elif first["media"]:
                sample = f"{first['media'][0]['type']} saved at {first['media'][0]['path']}"
        t.add_row([str(i), chat["name"], sample])

    print(t.get_string(title=f"Your {len(chats)} Chats (sampled)"))


def main():
    driver = set_up_driver()
    try:
        if not whatsapp_load(driver):
            print("Error loading whatsapp...")
            return

        chats = get_chats(driver)

        if chats:
            print_msg(chats)
        else:
            print("No chats found!")

    finally:
        print("Closing browser...")
        driver.quit()


if __name__ == '__main__':
    main()