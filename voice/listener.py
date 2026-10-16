import os
import sys
import contextlib
import subprocess
import speech_recognition as sr

# Set ALSA & JACK environment overrides
os.environ["ALSA_PLUGIN_DIR"] = "/usr/lib/x86_64-linux-gnu/alsa-lib"
os.environ["JACK_NO_START_SERVER"] = "1"

@contextlib.contextmanager
def suppress_c_stderr():
    """Suppresses low-level C ALSA/JACK stderr output."""
    try:
        sys.stderr.flush()
        old_stderr = os.dup(2)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 2)
        os.close(devnull)
        try:
            yield
        finally:
            os.dup2(old_stderr, 2)
            os.close(old_stderr)
    except Exception:
        yield

# Silence ALSA C-library errors
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

# Ensure microphone volume is optimal via PipeWire/WirePlumber
try:
    subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SOURCE@", "0.85"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except Exception:
    pass

recognizer = sr.Recognizer()
recognizer.energy_threshold = 250
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 1.8
recognizer.non_speaking_duration = 0.8

STOP_PHRASES = [
    "stop", "cancel", "halt", "pause", "wait",
    "থামো", "স্টপ", "দাঁড়াও", "থেমে যাও", "বাতিল", "বাদ দাও", "দরকার নাই", "করো না"
]

def is_stop_command(text: str) -> bool:
    """Checks if text contains an urgent stop/cancel keyword."""
    if not text:
        return False
    t = text.lower().strip()
    return any(p in t for p in STOP_PHRASES)

def get_best_microphone():
    """Finds best input microphone (Default Source or PipeWire)."""
    with suppress_c_stderr():
        try:
            device_names = sr.Microphone.list_microphone_names()
            # Prioritize Default Source (device 9) or PipeWire (device 6)
            for idx, name in enumerate(device_names):
                if "default source" in name.lower():
                    return sr.Microphone(device_index=idx)
            for idx, name in enumerate(device_names):
                if "pipewire" in name.lower():
                    return sr.Microphone(device_index=idx)
            for idx, name in enumerate(device_names):
                if "default" in name.lower():
                    return sr.Microphone(device_index=idx)
            return sr.Microphone()
        except Exception:
            return None

def record_ffmpeg_native(output_path="/tmp/jarvis_rec.wav", duration=5) -> bool:
    """Native PulseAudio recording fallback via ffmpeg."""
    cmd = [
        "ffmpeg", "-y", "-loglevel", "quiet",
        "-f", "pulse", "-i", "default",
        "-t", str(duration),
        "-ar", "16000", "-ac", "1",
        output_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            return True
    except Exception:
        pass
    return False

def listen_command(phrase_time_limit=90) -> str:
    """
    Continuous voice listener:
    - Captures from high-volume PipeWire default source.
    - Accurately parses Bengali (bn-BD) and English (en-US).
    - NEVER drops to text typing automatically; continuously listens for your voice!
    """
    mic = get_best_microphone()

    if mic is not None:
        try:
            with suppress_c_stderr():
                with mic as source:
                    print("\n🎙️ Listening... (Speak in Bangla or English)")
                    audio = recognizer.listen(source, timeout=7, phrase_time_limit=phrase_time_limit)

            print("⏳ Processing speech...")
            # 1. Recognize Bengali
            try:
                text = recognizer.recognize_google(audio, language="bn-BD")
                if text and text.strip():
                    print(f"👤 You said: \"{text.strip()}\"")
                    return text.strip()
            except sr.UnknownValueError:
                pass

            # 2. Recognize English
            try:
                text = recognizer.recognize_google(audio, language="en-US")
                if text and text.strip():
                    print(f"👤 You said: \"{text.strip()}\"")
                    return text.strip()
            except sr.UnknownValueError:
                pass

            print("❓ Could not understand audio. Listening again...")
            return ""

        except sr.WaitTimeoutError:
            return ""
        except Exception as e:
            # If PyAudio stream failed, fallback to native ffmpeg pulse recording
            pass

    # Native ffmpeg Pulse fallback
    temp_wav = "/tmp/jarvis_pulse_stream.wav"
    print("\n🎙️ Listening via native audio... (speak now)")
    if record_ffmpeg_native(temp_wav, duration=5):
        print("⏳ Processing speech...")
        try:
            with sr.AudioFile(temp_wav) as source:
                audio = recognizer.record(source)
            for lang in ["bn-BD", "en-US"]:
                try:
                    text = recognizer.recognize_google(audio, language=lang)
                    if text and text.strip():
                        print(f"👤 You said: \"{text.strip()}\"")
                        return text.strip()
                except sr.UnknownValueError:
                    continue
        except Exception:
            pass

    return ""
