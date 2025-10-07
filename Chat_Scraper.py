import os
import csv
import re

from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementNotInteractableException
from prettytable import PrettyTable
from dotenv import load_dotenv
from timeit import default_timer as timer
from prettytable import PrettyTable

def set_up_driver():
    # Configure selenium to use chrome webdriver
    load_dotenv()
    DRIVER_PATH = os.getenv('DRIVER_PATH')
    CHROME_PROFILE = os.getenv('CHROME_PROFILE')
    options = webdriver.ChromeOptions()
    # options.add_argument(f"user-data-dir={CHROME_PROFILE}")
    service = Service(DRIVER_PATH)
    driver = webdriver.Chrome(service = service, options=options)
    driver.set_script_timeout(90)
    
    return driver

def Check_User_Log_In(driver, wait_time):
    # Checks if the user is logged in to WhatsApp by looking for the presence chat pane in div element
    try:
        chat_pane = WebDriverWait(driver, wait_time).until(expected_conditions.presence_of_element_located((By.ID, 'pane-side')))
        return True
    except TimeoutException:
        return False

def whatsapp_load(driver):
    # Start whatsapp.web in the browser
    print("Running Whatsapp...",end="\r")
    driver.get('https://web.whatsapp.com/')
    
    # Checks if user is logged in or not
    logged_in, wait_time = False, 20
    while not logged_in:
        logged_in = Check_User_Log_In(driver, wait_time)
        
        # Allow user to try again and extend the wait time for Whatsapp to reload
        if not logged_in:
            # display error message
            print(f"Error: WhatsApp failed to load within {wait_time} seconds. Make sure you are logged in and try again.")
            is_valid_response = False
            while not is_valid_response:
                # Asks the user to login again
                err_response = input("Proceed  Yes(Y) or No(N) ?")
                if err_response.strip().lower() in {'y','yes'}:
                    is_valid_response = True
                    continue
                # Abort loading WhatsApp
                elif err_response.strip().lower() in {'n', 'no'}:
                    is_valid_response = True
                    return False
                # Re-prompt the question
                else:
                    is_valid_response = False
                    continue 
    # Success
    print("Success! WhatsApp finished loading and is ready.")
    return True   

def get_chats(driver):
    """
    Traverses WhatsApp Web chat-pane and collects Chat Info dynamically.
    """

    print("Loading your chats...", end="\r")

    def classify_chat(name, last_msg_sender):
        if last_msg_sender:
            return "group"
        elif name and (name.startswith("+") or name.replace(" ", "").isdigit()):
            return "unknown"
        else:
            return "contact"

    def analyze_sentiment(message):
        positive_words = {"good", "great", "happy", "love", "thanks", "awesome"}
        negative_words = {"bad", "sad", "angry", "hate", "sorry", "problem"}
        msg_lower = message.lower()
        if any(word in msg_lower for word in positive_words):
            return "positive"
        elif any(word in msg_lower for word in negative_words):
            return "negative"
        return "neutral"

    def message_length_category(message):
        length = len(message)
        if length < 20:
            return "short"
        elif length < 100:
            return "medium"
        return "long"

    def classify_day(time_str):
        if "today" in time_str.lower():
            return "today"
        elif "yesterday" in time_str.lower():
            return "yesterday"
        elif re.match(r"\d{1,2}/\d{1,2}/\d{4}", time_str):
            return "older"
        return "unknown"

    def contains_emoji(message):
        return bool(re.search(r"[\U0001F600-\U0001F64F"
                              r"\U0001F300-\U0001F5FF"
                              r"\U0001F680-\U0001F6FF"
                              r"\U0001F1E0-\U0001F1FF]", message))

    def compute_priority(unread, sentiment):
        if unread and sentiment == "negative":
            return "high"
        elif unread:
            return "medium"
        return "low"

    chats = []

    try:
        # Wait for chat pane
        chat_pane = WebDriverWait(driver, 20).until(
            expected_conditions.presence_of_element_located((By.ID, "pane-side"))
        )

        # Get chat rows
        chat_rows = chat_pane.find_elements(By.CSS_SELECTOR, "div[role='row']")

        for row in chat_rows[:20]:  # limit to first 20 for demo
            try:
                name = row.find_element(By.CSS_SELECTOR, "span[title]").get_attribute("title")
            except:
                name = "Unknown"

            try:
                last_msg = row.find_element(By.CSS_SELECTOR, "div[aria-label] span[dir='ltr']").text
            except:
                last_msg = ""

            try:
                last_time = row.find_element(By.CSS_SELECTOR, "div[aria-label] span[dir='auto']").text
            except:
                last_time = ""

            try:
                unread = bool(row.find_elements(By.CSS_SELECTOR, "span[aria-label*='unread']"))
            except:
                unread = False

            chat_type = classify_chat(name, None)
            sentiment = analyze_sentiment(last_msg)
            length_cat = message_length_category(last_msg)
            day_class = classify_day(last_time)
            emoji_flag = contains_emoji(last_msg)
            priority = compute_priority(unread, sentiment)

            chats.append({
                "name": name,
                "time": last_time,
                "message": last_msg,
                "type": chat_type,
                "sentiment": sentiment,
                "unread": unread,
                "meta": {
                    "length_category": length_cat,
                    "day_classification": day_class,
                    "contains_emoji": emoji_flag,
                    "priority": priority
                }
            })

        print("✅ Success! Your chats with sentiment analysis have been loaded.")

    except Exception as e:
        print("⚠️ Error while scraping chats:", e)

    return chats

def print_msg(chats):
    """
    Prints a summary of the scraped chats with Sentiment Analysis:
    - Chat type (contact/group/unknown)
    - Sentiment (positive/negative/neutral)
    - Unread flag
    - Priority and metadata
    """
    # Create a pretty table
    t = PrettyTable()
    t.field_names = ["#", "Chat Name", "Type", "Unread", "Sentiment", "Priority", "Last Msg Time", "Last Msg"]

    # Style the columns
    for key in t.align.keys():
        t.align[key] = "l"
    t._max_width = {
        "#": 3,
        "Chat Name": 20,
        "Type": 8,
        "Unread": 6,
        "Sentiment": 10,
        "Priority": 8,
        "Last Msg Time": 12,
        "Last Msg": 40
    }

    # Add up to 5 most recent chat records
    for i, chat in enumerate(chats[:5], start=1):
        t.add_row([
            str(i),
            chat.get("name", ""),
            chat.get("type", ""),
            "✔" if chat.get("unread") else "",
            chat.get("sentiment", ""),
            chat.get("meta", {}).get("priority", ""),
            chat.get("time", ""),
            chat.get("message", "")
        ])

    # Print the table
    print(t.get_string(title=f"Your {len(chats[:5])} Most Recent WhatsApp Chats"))


    
def main():
    # Use this function to control chrome browser automatically
    driver = set_up_driver()
    
    try:
        if not whatsapp_load(driver):
            print("Error loading whatsapp...")
            return 
        
        chat = get_chats(driver)
        
        if chat:
            print_msg(chat)
        else:
            print("No msg found!")
            
    finally:
        print("Closing browser...")
        driver.quit()
    

if __name__ == '__main__':
    main()
    