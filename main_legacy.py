import os
import sys
import ctypes
import json
import urllib.request
import webbrowser
import subprocess
import datetime
import speech_recognition as sr

# Suppress noisy ALSA / Jack / PulseAudio debug spam on Linux
try:
    ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)
    def py_error_handler(filename, line, function, err, fmt):
        pass
    c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
    asound = ctypes.cdll.LoadLibrary('libasound.so.2')
    asound.snd_lib_error_set_handler(c_error_handler)
except Exception:
    pass

# Load API Keys
gemini_key = os.getenv("GEMINI_API_KEY", "")
openai_key = os.getenv("OPENAI_API_KEY", "")

try:
    import config
    g_key = getattr(config, "gemini_api_key", "").strip()
    o_key = getattr(config, "openai_api_key", "").strip()
    c_key = getattr(config, "apikey", "").strip()

    if g_key and g_key != "your-gemini-api-key-here":
        gemini_key = g_key
    elif c_key and not c_key.startswith("sk-") and c_key != "your-openai-api-key-here":
        gemini_key = c_key

    if o_key and o_key != "your-openai-api-key-here":
        openai_key = o_key
    elif c_key and c_key.startswith("sk-"):
        openai_key = c_key
except ImportError:
    pass

from voice import speak, winSpeak


def open_media_or_file(file_path):
    """Opens a file or media player across Windows, Linux, and macOS."""
    if not os.path.exists(file_path):
        print(f"[File Error]: File not found at {file_path}")
        return False

    if sys.platform.startswith("win"):
        os.startfile(file_path)
    elif sys.platform.startswith("darwin"):
        subprocess.Popen(["open", file_path])
    else:
        subprocess.Popen(["xdg-open", file_path])
    return True


ACTIVE_GEMINI_MODEL = None


def get_available_gemini_models(api_key):
    """Fetches list of supported generateContent models from user's Gemini project."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    models = []
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for m in data.get("models", []):
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in methods:
                    name = m.get("name", "").replace("models/", "")
                    models.append(name)
    except Exception:
        pass
    return models


def call_gemini_direct_rest(prompt, api_key, system_instruction=None):
    """Direct REST API call to Google Gemini — requires ZERO third-party SDK packages."""
    global ACTIVE_GEMINI_MODEL
    full_prompt = f"{system_instruction}\n\nUser: {prompt}" if system_instruction else prompt
    last_error = None

    if ACTIVE_GEMINI_MODEL:
        models_to_try = [ACTIVE_GEMINI_MODEL]
    else:
        # Try current models first
        models_to_try = [
            "gemini-3.5-flash",
            "gemini-3.8-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-pro-preview",
            "gemini-flash-latest"
        ]
        # Dynamically discover supported models if needed
        discovered = get_available_gemini_models(api_key)
        for d in discovered:
            if d not in models_to_try:
                models_to_try.append(d)

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": full_prompt}]
                }
            ]
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if text:
                    ACTIVE_GEMINI_MODEL = model
                    return text
        except urllib.error.HTTPError as e:
            try:
                err_json = json.loads(e.read().decode("utf-8"))
                last_error = err_json.get("error", {}).get("message", str(e))
            except Exception:
                last_error = str(e)
        except Exception as e:
            last_error = str(e)

    if last_error:
        print(f"[Gemini API Error]: {last_error}")
    return None


def call_gemini_api(prompt, system_instruction=None):
    """Calls Google Gemini API with direct REST (prioritizing current models) or SDKs."""
    if not gemini_key or gemini_key == "your-gemini-api-key-here":
        return None

    # 1. Direct REST call (fastest, guaranteed compatibility with current models)
    rest_result = call_gemini_direct_rest(prompt, gemini_key, system_instruction)
    if rest_result:
        return rest_result

    # 2. Try google-genai SDK if available
    full_prompt = f"{system_instruction}\n\nUser: {prompt}" if system_instruction else prompt
    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
        for m in ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite"]:
            try:
                response = client.models.generate_content(model=m, contents=full_prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception:
                continue
    except ImportError:
        pass

    return None



def call_openai_chat(messages, max_tokens=256, temperature=1.0):
    """Calls OpenAI API if configured."""
    if not openai_key or openai_key == "your-openai-api-key-here":
        return None

    try:
        import openai
        if hasattr(openai, "OpenAI"):
            client = openai.OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        else:
            openai.api_key = openai_key
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[OpenAI Error]: {e}")
        return None


def get_ai_response(prompt, is_chat=True):
    """Routes query to Gemini first, then OpenAI, with concise responses for voice."""
    sys_prompt = (
        "You are JARVIS, an intelligent, polite, and witty AI voice assistant created by Tony Stark. "
        "Keep your response natural, short, and conversational (1 to 2 sentences max) suitable for voice speech."
        if is_chat else
        "You are an intelligent AI assistant. Provide a clear and helpful answer."
    )

    # 1. Try Gemini if key is present
    if gemini_key:
        res = call_gemini_api(prompt, system_instruction=sys_prompt)
        if res:
            return res
        return "Sir, I was unable to get a response from Gemini. Please check the terminal for the error details."

    # 2. Try OpenAI if key is present
    if openai_key:
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}
        ]
        res = call_openai_chat(messages)
        if res:
            return res
        return "Sir, I was unable to get a response from OpenAI. Please check the terminal."

    # 3. No key configured
    msg = "Sir, please configure your Gemini API key in config.py."
    print(f"[Warning] {msg}")
    return msg



def ai(query):
    print(f"\n[AI Task]: {query}")
    speak("Processing your request with artificial intelligence, sir...")

    response_content = get_ai_response(query, is_chat=False)
    text = f"AI response for Prompt: {query}\n{'=' * 45}\n\n{response_content}"

    if not os.path.exists("AI_Responses"):
        os.mkdir("AI_Responses")

    file_title = ''.join(query.split('intelligence')[1:]).strip() if 'intelligence' in query.lower() else query
    safe_filename = "".join(c for c in file_title if c.isalnum() or c in (' ', '_', '-')).strip()
    if not safe_filename:
        safe_filename = "response"

    save_path = os.path.join("AI_Responses", f"{safe_filename[:50]}.txt")
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)

    speak(f"Sir, I have generated and saved the response in the AI Responses folder.")


def chat(query):
    print(f"\n[Thinking...]")
    response_text = get_ai_response(query, is_chat=True)
    speak(response_text)
    return response_text


try:
    import pyaudio
except Exception:
    pyaudio = None

# Initialize recognizer once globally
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8


WORKING_MIC = None


def get_working_microphone():
    """Auto-detects and verifies a working microphone input device."""
    global WORKING_MIC
    if WORKING_MIC is not None:
        return WORKING_MIC

    if pyaudio is None:
        return None

    p = None
    try:
        p = pyaudio.PyAudio()
        count = p.get_device_count()

        candidates = []
        for i in range(count):
            try:
                info = p.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) > 0:
                    candidates.append((i, info.get("name", "")))
            except Exception:
                continue

        # Sort priority: pulse/default first, then 'front' or 'alt' (front panel mic), then others
        def mic_priority(item):
            name = item[1].lower()
            if "pulse" in name or "default" in name:
                return 0
            if "front" in name or "alt" in name:
                return 1
            if "analog" in name:
                return 2
            return 3

        candidates.sort(key=mic_priority)

        # Find the first candidate that can successfully open a stream
        for idx, name in candidates:
            try:
                test_mic = sr.Microphone(device_index=idx)
                with test_mic as source:
                    pass
                print(f"🎙️  Microphone connected: '{name}' [Device ID: {idx}]")
                WORKING_MIC = test_mic
                return WORKING_MIC
            except Exception:
                continue

    except Exception as e:
        print(f"[Microphone Init Error]: {e}")
    finally:
        if p is not None:
            try:
                p.terminate()
            except Exception:
                pass

    return None



def record_native_pulse(output_path, duration=5):
    """Bypasses Anaconda/PortAudio bugs by using native Ubuntu PulseAudio to capture from Front Mic."""
    # 1. Try ffmpeg via pulse
    cmd_ffmpeg = [
        "ffmpeg", "-y", "-loglevel", "quiet",
        "-f", "pulse", "-i", "default",
        "-t", str(duration),
        "-ar", "16000", "-ac", "1",
        output_path
    ]
    try:
        res = subprocess.run(cmd_ffmpeg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            return True
    except Exception:
        pass

    # 2. Try arecord fallback
    cmd_arecord = [
        "arecord", "-q",
        "-f", "S16_LE", "-r", "16000", "-c", "1",
        "-d", str(duration),
        output_path
    ]
    try:
        res = subprocess.run(cmd_arecord, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            return True
    except Exception:
        pass

    return False


def takeCommand():
    """Listens for user speech via microphone with native PulseAudio fallback & text fallback."""
    mic = get_working_microphone()

    if mic is not None:
        try:
            with mic as source:
                print("\n🎙️  Listening... (speak now)")
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=10)

                print("⏳ Recognizing speech...")
                for lang in ["en-US", "en-IN", "bn-BD"]:
                    try:
                        text = recognizer.recognize_google(audio, language=lang)
                        if text and text.strip():
                            print(f"👤 You said: \"{text}\"")
                            return text.strip()
                    except sr.UnknownValueError:
                        continue

                print("❓ Could not understand audio. (Tip: Speak clearly or check Mic volume)")
                return ""

        except sr.WaitTimeoutError:
            return ""
        except Exception:
            pass

    # Method 2: Native PulseAudio recording from Front Microphone (Bypasses Anaconda ALSA conflict)
    temp_voice = "/tmp/jarvis_input.wav"
    print("\n🎙️  Listening... (speak now for 5 seconds)")
    if record_native_pulse(temp_voice, duration=5):
        print("⏳ Recognizing speech...")
        try:
            with sr.AudioFile(temp_voice) as source:
                audio = recognizer.record(source)
            for lang in ["en-US", "en-IN", "bn-BD"]:
                try:
                    text = recognizer.recognize_google(audio, language=lang)
                    if text and text.strip():
                        print(f"👤 You said: \"{text}\"")
                        return text.strip()
                except sr.UnknownValueError:
                    continue
        except Exception as e:
            print(f"[Speech Error]: {e}")
        print("❓ Could not understand audio.")
        return ""

    # Method 3: Text input fallback
    try:
        user_input = input("👤 You (Type query): ").strip()
        return user_input
    except (EOFError, KeyboardInterrupt):
        sys.exit(0)




if __name__ == "__main__":
    welcome_msg = "Hello sir, I am JARVIS. How may I assist you today?"
    speak(welcome_msg)

    sites = [
        ["youtube", "https://www.youtube.com"],
        ["instagram", "https://www.instagram.com"],
        ["facebook", "https://www.facebook.com"],
        ["wikipedia", "https://www.wikipedia.org"],
        ["google", "https://www.google.com"]
    ]

    while True:
        query = takeCommand()
        if not query:
            continue

        query_lower = query.lower()

        # 1. Open websites
        matched_site = False
        for site in sites:
            if f"open {site[0]}" in query_lower:
                speak(f"Opening {site[0]} sir...")
                webbrowser.open(site[1])
                matched_site = True
                break

        if matched_site:
            continue

        # 2. Open music
        if "open music" in query_lower or "play music" in query_lower:
            musicPath = os.path.join("Music", "raj.mp3")
            speak("Opening music, sir.")
            if not open_media_or_file(musicPath):
                speak("Sir, the music file was not found in the Music folder.")

        # 3. Artificial intelligence generation
        elif "using artificial intelligence" in query_lower:
            ai(query)

        # 4. Manual query input
        elif "input query" in query_lower:
            user_input = input("Enter any query: ")
            speak(f"Sir, your query is {user_input}")
            ai(user_input)

        # 5. Tell Time
        elif "the time" in query_lower or "what time" in query_lower:
            now = datetime.datetime.now()
            hour = now.strftime("%I:%M %p")
            speak(f"Sir, the current time is {hour}.")

        # 6. Exit
        elif "jarvis quit" in query_lower or "exit" in query_lower or "bye" in query_lower:
            speak("Goodbye sir, have a great day!")
            sys.exit(0)

        # 7. General AI conversation
        else:
            chat(query)