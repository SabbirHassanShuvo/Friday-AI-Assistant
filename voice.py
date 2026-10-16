import os
import platform
import subprocess
import tempfile

try:
    import pyttsx3
    _engine = pyttsx3.init()
    # Set speech rate and volume for clarity
    _engine.setProperty('rate', 155)
    _engine.setProperty('volume', 1.0)
except Exception:
    _engine = None


def play_audio_file(file_path):
    """Plays an audio file cleanly using available system players."""
    # 1. ffplay (usually available on Ubuntu with ffmpeg)
    try:
        res = subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if res.returncode == 0:
            return True
    except FileNotFoundError:
        pass

    # 2. mpg123
    try:
        res = subprocess.run(
            ["mpg123", "-q", file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if res.returncode == 0:
            return True
    except FileNotFoundError:
        pass

    # 3. playsound
    try:
        import playsound
        playsound.playsound(file_path)
        return True
    except Exception:
        pass

    # 4. paplay (for wav) or aplay
    if file_path.endswith(".wav"):
        try:
            subprocess.run(["paplay", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            try:
                subprocess.run(["aplay", "-q", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except FileNotFoundError:
                pass

    return False


def speak(query):
    """Speaks text using natural, clear voice (gTTS), with offline fallback."""
    if not query or not query.strip():
        return

    print(f"[JARVIS]: {query}")

    # Method 1: Natural, clear human voice with gTTS
    try:
        from gtts import gTTS
        tts = gTTS(text=query, lang="en", tld="com")
        temp_audio = os.path.join(tempfile.gettempdir(), "jarvis_voice.mp3")
        tts.save(temp_audio)
        if play_audio_file(temp_audio):
            return
    except Exception:
        pass

    # Method 2: pyttsx3 (offline fallback)
    if _engine is not None:
        try:
            _engine.say(query)
            _engine.runAndWait()
            return
        except Exception:
            pass

    # Method 3: Linux system speech engines
    if platform.system() != "Windows":
        for cmd in ["spd-say", "espeak-ng", "espeak"]:
            try:
                subprocess.run([cmd, query], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except (subprocess.SubprocessError, FileNotFoundError):
                continue

    # Method 4: Windows SAPI
    if platform.system() == "Windows":
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak(query)
            return
        except Exception:
            pass


def winSpeak(query):
    """Backward-compatible alias for speak."""
    speak(query)


def gttsSpeak(query):
    speak(query)
