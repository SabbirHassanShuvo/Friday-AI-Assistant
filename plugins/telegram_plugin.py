import os
import asyncio
from plugins.base import BasePlugin
from core.tool_registry import tool
from automation.os_manager import open_application, open_url_tab

class TelegramPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "telegram_plugin"

    @property
    def description(self) -> str:
        return "Reads recent Telegram messages, checks unread chats, and sends messages."

    def register_tools(self):
        @tool(name="check_telegram_messages", description="Checks recent Telegram chats and identifies who sent the last message.")
        def check_telegram_messages() -> str:
            # Check if Telegram API credentials are configured
            api_id = os.getenv("TELEGRAM_API_ID", "")
            api_hash = os.getenv("TELEGRAM_API_HASH", "")

            try:
                import config
                api_id = getattr(config, "telegram_api_id", api_id)
                api_hash = getattr(config, "telegram_api_hash", api_hash)
            except Exception:
                pass

            if not api_id or not api_hash:
                # Open Web/Desktop Telegram fallback
                open_application("telegram-desktop")
                return ("Telegram API is not configured in config.py yet. "
                        "I have opened Telegram Desktop for you. "
                        "To enable direct AI reading, add your telegram_api_id and api_hash.")

            # Connect via Telethon
            try:
                from telethon import TelegramClient
                session_path = os.path.expanduser("~/.jarvis_telegram.session")
                
                async def _get_chats():
                    async with TelegramClient(session_path, int(api_id), api_hash) as client:
                        dialogs = await client.get_dialogs(limit=3)
                        msgs = []
                        for d in dialogs:
                            sender = d.name
                            last_msg = d.message.message if d.message else "Media/File"
                            msgs.append(f"{sender}: '{last_msg}'")
                        return "; ".join(msgs)

                res = asyncio.run(_get_chats())
                return f"Recent Telegram messages: {res}"
            except Exception as e:
                return f"Telegram check error: {e}"

        @tool(name="send_telegram_message", description="Sends a message to a Telegram contact or group.")
        def send_telegram_message(recipient: str, message: str) -> str:
            api_id = os.getenv("TELEGRAM_API_ID", "")
            api_hash = os.getenv("TELEGRAM_API_HASH", "")
            try:
                import config
                api_id = getattr(config, "telegram_api_id", api_id)
                api_hash = getattr(config, "telegram_api_hash", api_hash)
            except Exception:
                pass

            if not api_id or not api_hash:
                open_url_tab(f"https://t.me/{recipient.replace('@', '')}")
                return f"Opened Telegram chat link for {recipient}."

            try:
                from telethon import TelegramClient
                session_path = os.path.expanduser("~/.jarvis_telegram.session")
                
                async def _send():
                    async with TelegramClient(session_path, int(api_id), api_hash) as client:
                        await client.send_message(recipient, message)
                        return True

                asyncio.run(_send())
                return f"Successfully sent Telegram message to {recipient}."
            except Exception as e:
                return f"Failed to send Telegram message: {e}"

# Auto-instantiate and register tools
telegram_plugin = TelegramPlugin()
telegram_plugin.register_tools()
