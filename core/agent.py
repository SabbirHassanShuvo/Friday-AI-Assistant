import os
from google import genai
from google.genai import types
from core.tool_registry import registry
from voice.speaker import stop_audio
import config

# Import all plugins to register tools
import plugins.system_plugin
import plugins.web_agent_plugin
import plugins.whatsapp_plugin
import plugins.telegram_plugin
import plugins.social_plugin
import plugins.mail_plugin

SYSTEM_INSTRUCTION = """
You are JARVIS, an elite, highly capable, polite, and witty AI personal assistant.
You serve your master with ultimate efficiency and precision.

You have direct access to tools for:
- Default Google Chrome (opening websites, social media with existing logged-in sessions)
- WhatsApp Web (checking recent messages, sending messages)
- Telegram (checking recent messages, sending messages)
- Facebook, Instagram, YouTube, LinkedIn (opening directly in primary Chrome, checking notifications/DMs, posting updates)
- Gmail (checking unread emails, drafting emails)
- System and OS operations (opening software like Chrome, VS Code, Terminal, Spotify, volume control, time, system health)
- Web Automation (querying ChatGPT, searching YouTube, DuckDuckGo instant answers)

Crucial Behavioral Rules:
1. Multi-Step Execution: If the user provides a long or compound prompt with multiple commands (e.g., 'open Chrome, then open Facebook, and tell me the battery status'), execute all the required tools sequentially one by one without skipping any step.
2. Stop / Cancel Handling: If the user says 'stop', 'cancel', 'থামো', 'বাদ দাও', 'থেমে যাও', or 'করো না', immediately stop, confirm with 'জি স্যার, কাজ থামিয়ে দিয়েছি', and do not execute pending actions.
3. Default Chrome: Always open websites and social media platforms using the user's default primary Google Chrome.
4. Response Tone: If the user speaks in Bengali, reply in polite, fluent Bengali. If in English, reply in English. Keep spoken responses punchy, fast, and natural (1 to 2 sentences max).
5. Multi-Turn Context: Maintain memory across conversation turns.
"""

MODELS_LIST = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-3.8-flash"
]

class JarvisAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or getattr(config, "gemini_api_key", "")
        self.client = genai.Client(api_key=self.api_key)
        self.model_index = 0
        self.model_name = MODELS_LIST[self.model_index]
        self._init_chat_session()

    def _init_chat_session(self):
        """Initializes a stateful chat session with automatic function calling enabled."""
        callable_tools = registry.get_all_tools()
        self.chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=callable_tools,
                temperature=0.4
            )
        )

    def _switch_to_next_model(self):
        """Switches to backup model if quota is exhausted."""
        self.model_index = (self.model_index + 1) % len(MODELS_LIST)
        self.model_name = MODELS_LIST[self.model_index]
        print(f"\n[Agent]: Switching to backup model '{self.model_name}'...")
        self._init_chat_session()

    def cancel_active_operations(self):
        """Stops active audio playback and resets state."""
        stop_audio()

    def process_query(self, user_query: str) -> str:
        """Processes user voice/text query, executes multi-step tools automatically, and returns reply."""
        if not user_query or not user_query.strip():
            return ""

        query_clean = user_query.strip()
        print(f"\n[Agent Processing]: \"{query_clean}\"")

        # Fast stop check
        stop_keywords = ["stop", "cancel", "halt", "থামো", "স্টপ", "বাদ দাও", "থেমে যাও", "দরকার নাই", "করো না"]
        if any(w in query_clean.lower() for w in stop_keywords):
            self.cancel_active_operations()
            return "জি স্যার, কাজটি থামিয়ে দিয়েছি।"

        for _ in range(len(MODELS_LIST)):
            try:
                response = self.chat.send_message(query_clean)
                if response and response.text:
                    return response.text.strip()
                return "Task completed, sir."
            except Exception as e:
                err_msg = str(e)
                print(f"[Agent Model Error ({self.model_name})]: {err_msg[:80]}")
                if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg or "NOT_FOUND" in err_msg:
                    self._switch_to_next_model()
                    continue
                else:
                    try:
                        self._init_chat_session()
                        response = self.chat.send_message(query_clean)
                        if response and response.text:
                            return response.text.strip()
                    except Exception:
                        pass
                    return f"Sir, I encountered an issue: {e}"

        return "Sir, all Gemini models are currently rate limited. Please retry in a few moments."

agent = JarvisAgent()
