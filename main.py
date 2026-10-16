#!/usr/bin/env python3
"""
JARVIS - Advanced Autonomous AI Personal Assistant
Engineered with Gemini Automatic Function Calling (AFC),
Playwright Browser Automation, and Neural Edge-TTS.
"""

import sys
import os

# 1. System-wide Audio & ALSA Overrides (Must be before any imports)
os.environ["ALSA_PLUGIN_DIR"] = "/usr/lib/x86_64-linux-gnu/alsa-lib"
os.environ["JACK_NO_START_SERVER"] = "1"

# Silence C-level ALSA error handler
try:
    import ctypes
    ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)
    def py_error_handler(filename, line, function, err, fmt):
        pass
    c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
    asound = ctypes.cdll.LoadLibrary("libasound.so.2")
    asound.snd_lib_error_set_handler(c_error_handler)
except Exception:
    pass

from voice.speaker import speak, stop_audio
from voice.listener import listen_command, is_stop_command
from core.agent import agent

BANNER = """
============================================================
       ⚡ J.A.R.V.I.S. - Autonomous AI Assistant ⚡
============================================================
 [Plugins Active]:
   • Default Google Chrome Browser Integration
   • WhatsApp Web Automation (Read / Send)
   • Telegram Client (Read / Send)
   • Social Media (Facebook, Instagram, LinkedIn, YouTube)
   • Gmail (Inbox Check & Drafts)
   • OS & Software Control (Apps, Volume, Health)
   • Web & ChatGPT Agent (Instant Research)
 [Speech & Voice]:
   • Pure Continuous Voice Mode (Auto-boosted mic input)
   • 100% Clean Terminal (No ALSA/JACK spam)
   • Faster +18% Neural Edge-TTS (English & Bengali)
   • Instant Stop / Cancellation Control ('থামো', 'স্টপ', 'বাদ দাও')
============================================================
"""

def main():
    print(BANNER)
    welcome_msg = "Hello sir, I am JARVIS. All autonomous systems and plugins are online. How may I assist you?"
    speak(welcome_msg)

    text_mode = "--text" in sys.argv

    while True:
        try:
            # 1. Listen for voice command or optional text mode
            if text_mode:
                user_input = input("\n👤 You (Type query): ").strip()
            else:
                user_input = listen_command()

            if not user_input or not user_input.strip():
                continue

            query = user_input.strip()
            query_lower = query.lower()

            # 2. Check for instant stop / cancel commands
            if is_stop_command(query):
                stop_audio()
                agent.cancel_active_operations()
                stop_ack = "জি স্যার, কাজটি থামিয়ে দিয়েছি।"
                speak(stop_ack)
                continue

            # 3. Check for exit commands
            if any(w in query_lower for w in ["exit", "quit", "goodbye", "jarvis shutdown", "বিদায়", "বন্ধ হও"]):
                farewell = "Goodbye sir, standing by whenever you need me."
                speak(farewell)
                sys.exit(0)

            # 4. Process via Autonomous Agent (Triggers tools automatically)
            response = agent.process_query(query)

            # 5. Speak response back to user
            if response:
                speak(response)

        except KeyboardInterrupt:
            print("\n[JARVIS]: Interrupted by user. Exiting...")
            stop_audio()
            sys.exit(0)
        except Exception as e:
            print(f"\n[JARVIS System Error]: {e}")
            speak("Sir, I encountered a temporary processing error.")

if __name__ == "__main__":
    main()