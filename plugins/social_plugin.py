import time
from playwright.sync_api import sync_playwright
from plugins.base import BasePlugin
from core.tool_registry import tool
from automation.browser_agent import browser

class SocialMediaPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "social_media_plugin"

    @property
    def description(self) -> str:
        return "Manages Facebook, Instagram, and LinkedIn: reads notifications, checks messages, and posts updates."

    def register_tools(self):
        @tool(name="check_facebook_last_activity", description="Checks Facebook notifications and Messenger for who sent the last message.")
        def check_facebook_last_activity() -> str:
            print("\n[Social Agent]: Checking Facebook Messenger and notifications...")
            with sync_playwright() as p:
                context = browser.get_context(p, headless=True)
                page = context.new_page()
                try:
                    page.goto("https://www.facebook.com/messages", timeout=30000)
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(3)

                    if "login" in page.url.lower():
                        return "Sir, Facebook is not logged in. Say 'login facebook' to open the browser and login once."

                    # Check recent conversations
                    convs = page.locator('div[role="navigation"] div[role="row"]').all()
                    if convs:
                        top_conv = convs[0].inner_text().split("\n")
                        sender = top_conv[0] if top_conv else "Unknown"
                        msg = top_conv[1] if len(top_conv) > 1 else ""
                        return f"Last message on Facebook Messenger is from {sender}: '{msg}'"
                    return "Checked Facebook: No new unread messages found."
                except Exception as e:
                    return f"Could not check Facebook: {e}"
                finally:
                    context.close()

        @tool(name="post_status_facebook", description="Posts a text status update to user's Facebook profile.")
        def post_status_facebook(post_text: str) -> str:
            print(f"\n[Social Agent]: Posting to Facebook: '{post_text}'...")
            with sync_playwright() as p:
                context = browser.get_context(p, headless=False)
                page = context.new_page()
                try:
                    page.goto("https://www.facebook.com", timeout=30000)
                    time.sleep(3)

                    if "login" in page.url.lower():
                        return "Facebook is not logged in. Please login first."

                    # Look for "What's on your mind?" post trigger
                    trigger = page.locator('div[role="button"]:has-text("What\'s on your mind")').first
                    if trigger.is_visible():
                        trigger.click()
                        time.sleep(2)
                        
                        # Type text in post dialog
                        post_input = page.locator('div[role="textbox"][contenteditable="true"]').first
                        post_input.fill(post_text)
                        time.sleep(1)
                        
                        # Click "Post" button
                        post_btn = page.locator('div[aria-label="Post"][role="button"]').first
                        if post_btn.is_visible():
                            post_btn.click()
                            time.sleep(3)
                            return f"Successfully posted to Facebook: '{post_text}'"
                    return "Opened Facebook post window, but could not auto-submit. Completed in browser."
                except Exception as e:
                    return f"Error posting to Facebook: {e}"
                finally:
                    context.close()

        @tool(name="check_instagram_dms", description="Checks Instagram direct messages (DMs) for recent chats.")
        def check_instagram_dms() -> str:
            print("\n[Social Agent]: Checking Instagram DMs...")
            with sync_playwright() as p:
                context = browser.get_context(p, headless=True)
                page = context.new_page()
                try:
                    page.goto("https://www.instagram.com/direct/inbox/", timeout=30000)
                    time.sleep(4)

                    if "login" in page.url.lower() or "accounts/login" in page.url.lower():
                        return "Instagram is not logged in. Say 'login instagram' to login once in the browser."

                    # Check inbox chats
                    chats = page.locator('div[role="listitem"]').all()
                    if chats:
                        top = chats[0].inner_text().split("\n")
                        sender = top[0] if top else "User"
                        msg = top[1] if len(top) > 1 else ""
                        return f"Last Instagram DM from {sender}: '{msg}'"
                    return "Checked Instagram: No unread DMs found."
                except Exception as e:
                    return f"Error checking Instagram: {e}"
                finally:
                    context.close()

        @tool(name="open_social_platform", description="Opens Facebook, Instagram, LinkedIn, YouTube, or Twitter directly in your primary Google Chrome.")
        def open_social_platform(platform: str) -> str:
            from automation.os_manager import open_url_tab
            p = platform.lower().strip()
            url_map = {
                "facebook": "https://www.facebook.com",
                "fb": "https://www.facebook.com",
                "instagram": "https://www.instagram.com",
                "insta": "https://www.instagram.com",
                "linkedin": "https://www.linkedin.com",
                "twitter": "https://x.com",
                "x": "https://x.com",
                "youtube": "https://www.youtube.com",
                "whatsapp": "https://web.whatsapp.com",
                "chatgpt": "https://chatgpt.com"
            }
            target_url = url_map.get(p, f"https://www.{p}.com")
            return open_url_tab(target_url)

# Auto-instantiate and register tools
social_plugin = SocialMediaPlugin()
social_plugin.register_tools()
