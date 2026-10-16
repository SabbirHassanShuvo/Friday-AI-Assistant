import time
import urllib.parse
from playwright.sync_api import sync_playwright
from plugins.base import BasePlugin
from core.tool_registry import tool
from automation.browser_agent import browser

class WhatsAppPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "whatsapp_plugin"

    @property
    def description(self) -> str:
        return "Manages WhatsApp Web: reads last messages, checks notifications, and sends messages."

    def register_tools(self):
        @tool(name="check_whatsapp_last_messages", description="Checks WhatsApp Web for recent messages, unread chats, and who sent the last message.")
        def check_whatsapp_last_messages() -> str:
            print("\n[WhatsApp Agent]: Checking recent WhatsApp messages...")
            with sync_playwright() as p:
                context = browser.get_context(p, headless=True)
                page = context.new_page()
                try:
                    page.goto("https://web.whatsapp.com", timeout=35000)
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(4)

                    # Check if QR code screen is present
                    qr_canvas = page.locator('canvas[aria-label="Scan this QR code to link a device"]')
                    if qr_canvas.count() > 0 or "landing-wrapper" in page.content():
                        return "Sir, WhatsApp Web is not logged in yet. Please say 'login whatsapp' to scan your QR code once."

                    # Wait for chat list pane
                    page.wait_for_selector('#pane-side', timeout=15000)
                    chats = page.locator('#pane-side div[role="listitem"]').all()
                    
                    if not chats:
                        return "No active conversations found on WhatsApp."

                    # Read top 2 recent chats
                    results = []
                    for chat in chats[:3]:
                        text = chat.inner_text().split("\n")
                        # Chat item usually has: Name, Time, Last message, Unread count
                        if len(text) >= 2:
                            contact_name = text[0]
                            last_msg = text[2] if len(text) > 2 else text[1]
                            time_val = text[1] if len(text) > 2 else ""
                            results.append(f"{contact_name}: '{last_msg}' ({time_val})")

                    if results:
                        summary = "; ".join(results)
                        return f"Recent WhatsApp chats: {summary}"
                    return "Could not parse WhatsApp message text."
                except Exception as e:
                    return f"WhatsApp check encountered an issue: {e}"
                finally:
                    context.close()

        @tool(name="send_whatsapp_message", description="Sends a WhatsApp message to a phone number or contact name.")
        def send_whatsapp_message(contact_or_number: str, message: str) -> str:
            print(f"\n[WhatsApp Agent]: Sending message to {contact_or_number}: '{message}'...")
            with sync_playwright() as p:
                context = browser.get_context(p, headless=False)
                page = context.new_page()
                try:
                    # If it's a numeric phone number (e.g. +88017... or 017...)
                    digits = "".join(c for c in contact_or_number if c.isdigit())
                    if len(digits) >= 10:
                        encoded_msg = urllib.parse.quote(message)
                        url = f"https://web.whatsapp.com/send?phone={digits}&text={encoded_msg}"
                        page.goto(url, timeout=35000)
                        page.wait_for_selector('span[data-icon="send"]', timeout=20000)
                        time.sleep(2)
                        page.locator('span[data-icon="send"]').click()
                        time.sleep(2)
                        return f"Message successfully sent to {contact_or_number}."

                    # Search by contact name in chat search bar
                    page.goto("https://web.whatsapp.com", timeout=35000)
                    page.wait_for_selector('#pane-side', timeout=15000)
                    
                    search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
                    search_box.fill(contact_or_number)
                    time.sleep(2)
                    page.keyboard.press("Enter")
                    time.sleep(2)

                    # Type message in active chat box
                    msg_box = page.locator('footer div[contenteditable="true"][data-tab="10"]')
                    if msg_box.is_visible():
                        msg_box.fill(message)
                        page.keyboard.press("Enter")
                        time.sleep(2)
                        return f"Message sent to {contact_or_number} on WhatsApp."
                    return f"Found contact {contact_or_number}, but could not focus message input."
                except Exception as e:
                    return f"Failed to send WhatsApp message: {e}"
                finally:
                    context.close()

        @tool(name="open_whatsapp_qr_login", description="Opens a visible browser for user to scan WhatsApp QR code.")
        def open_whatsapp_qr_login() -> str:
            browser.open_login_manager("https://web.whatsapp.com")
            return "WhatsApp login window opened. After scanning, your session will be saved forever."

# Auto-instantiate and register tools
whatsapp_plugin = WhatsAppPlugin()
whatsapp_plugin.register_tools()
