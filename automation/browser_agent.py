import os
import time
import urllib.parse
from playwright.sync_api import sync_playwright

BROWSER_DATA_DIR = os.path.expanduser("~/.jarvis_browser_profile")
os.makedirs(BROWSER_DATA_DIR, exist_ok=True)

class JarvisBrowser:
    """Manages persistent browser automation for WhatsApp, ChatGPT, and Social Media."""
    
    def __init__(self, headless=True):
        self.headless = headless

    def get_context(self, p, headless=None):
        if headless is None:
            headless = self.headless
        # Launch persistent context to preserve logins (WhatsApp, ChatGPT, FB, Insta)
        context = p.chromium.launch_persistent_context(
            user_data_dir=BROWSER_DATA_DIR,
            headless=headless,
            viewport={"width": 1280, "height": 800},
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"]
        )
        return context

    def query_chatgpt(self, prompt: str) -> str:
        """Navigates to ChatGPT, inputs the user's prompt, and extracts the response."""
        with sync_playwright() as p:
            # ChatGPT often challenges fully headless; visible or stealth context works best
            context = self.get_context(p, headless=self.headless)
            page = context.new_page()
            try:
                page.goto("https://chatgpt.com", timeout=30000)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(2)

                # Look for prompt input textarea or contenteditable div
                input_selector = '#prompt-textarea'
                if page.is_visible(input_selector):
                    page.fill(input_selector, prompt)
                    page.keyboard.press("Enter")
                    
                    # Wait for response generation to complete
                    time.sleep(5)
                    # Check for assistant message blocks
                    responses = page.locator('article[data-testid^="conversation-turn-"]').all()
                    if responses:
                        last_turn = responses[-1].inner_text()
                        return last_turn.strip()
                    return "ChatGPT prompt submitted, but could not capture completed text stream."
                else:
                    return "ChatGPT requires login or security verification. Please open browser profile to authenticate."
            except Exception as e:
                return f"Error interacting with ChatGPT: {e}"
            finally:
                context.close()

    def search_youtube(self, query: str) -> str:
        """Searches YouTube and plays the top result video."""
        encoded = urllib.parse.quote(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded}"
        with sync_playwright() as p:
            context = self.get_context(p, headless=False)  # Visible so user can watch/listen
            page = context.new_page()
            try:
                page.goto(search_url, timeout=20000)
                page.wait_for_selector('ytd-video-renderer a#video-title', timeout=10000)
                first_video = page.locator('ytd-video-renderer a#video-title').first
                title = first_video.inner_text()
                first_video.click()
                return f"Playing '{title}' on YouTube."
            except Exception as e:
                return f"Could not play video on YouTube: {e}"

    def open_login_manager(self, service_url: str):
        """Opens service in user's primary browser without freezing."""
        from automation.os_manager import open_url_tab
        open_url_tab(service_url)
        return f"Opened {service_url} in your primary Google Chrome."

browser = JarvisBrowser(headless=True)
