This project automates extraction of WhatsApp chats using Selenium web driver. It analyzes their sentiment, and display a summary in a clean tabular format. 

Features of WhatsApp_Scraper:
1. Automated WhatsApp Web login check
Ensures you’re logged in before scraping.
2. Chat scraping- Collects chat name, last message, timestamp, unread status.
3. Classification
4. Contact / Group / Unknown
5. Message length category (short / medium / long)
6. Day classification (today / yesterday / older)
7. Emoji detection
8. Sentiment analysis (basic)
9. Labels messages as positive, negative, or neutral.
10. Priority scoring
11. Unread + negative sentiment = high priority.
12. PrettyTable output: Displays the top 5 most recent chats in a formatted table.

🛠️ Requirements
- Python 3.8+
- Google Chrome installed
- ChromeDriver (matching your Chrome version)

⚙️ Setup
1. Clone this repository using:
git clone https://github.com/yourusername/whatsapp-chat-scraper.git

3. cd whatsapp-chat-scraper
4. Set environment variables
5. Create a .env file in the project root:
6. DRIVER_PATH=/path/to/chromedriver
7. CHROME_PROFILE=/path/to/your/chrome/profile
8. DRIVER_PATH: Path to your ChromeDriver executable.
9. CHROME_PROFILE: (Optional) Path to your Chrome user profile for persistent login.
10. Run the script using 
python main.py

11. Login to WhatsApp Web
- The script opens WhatsApp Web.
- If not logged in, scan the QR code.
- The script waits until the chat pane is detected.
