import os
import sys
import asyncio
import subprocess
import tempfile
import edge_tts

# Voice personas
VOICE_EN = "en-US-ChristopherNeural"  # Polished, intelligent JARVIS voice
VOICE_BN = "bn-BD-PradeepNeural"        # Natural Bengali male voice

CURRENT_AUDIO_PROCESS = None

def is_bengali(text: str) -> bool:
    """Checks if text contains Bengali Unicode characters."""
    return any('\u0980' <= c <= '\u09FF' for c in text)

def stop_audio():
    """Immediately stops any currently playing JARVIS audio."""
    global CURRENT_AUDIO_PROCESS
    if CURRENT_AUDIO_PROCESS is not None:
        try:
            CURRENT_AUDIO_PROCESS.terminate()
            CURRENT_AUDIO_PROCESS.kill()
        except Exception:
            pass
        CURRENT_AUDIO_PROCESS = None

    try:
        subprocess.run(["pkill", "-9", "-f", "ffplay.*jarvis"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

async def _generate_edge_speech(text: str, output_path: str, voice: str = None) -> bool:
    """Asynchronously generates audio file using Edge-TTS with +18% rate for faster response."""
    if not voice:
        voice = VOICE_BN if is_bengali(text) else VOICE_EN
    try:
        # rate="+18%" makes speech snappy, energetic, and natural
        communicate = edge_tts.Communicate(text, voice, rate="+18%")
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"[Edge-TTS Error]: {e}")
        return False

def play_audio(file_path: str):
    """Plays an audio file via ffplay with instant start and interruptibility."""
    global CURRENT_AUDIO_PROCESS
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return

    try:
        CURRENT_AUDIO_PROCESS = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-infbuf", file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        CURRENT_AUDIO_PROCESS.wait()
        CURRENT_AUDIO_PROCESS = None
        return
    except Exception:
        pass

    # Fallback to aplay / system player
    try:
        CURRENT_AUDIO_PROCESS = subprocess.Popen(
            ["aplay", "-q", file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        CURRENT_AUDIO_PROCESS.wait()
        CURRENT_AUDIO_PROCESS = None
    except Exception:
        pass

def speak(text: str, voice: str = None):
    """Speaks given text naturally and quickly with neural Edge-TTS."""
    if not text or not text.strip():
        return

    # Stop any previous playing audio first
    stop_audio()

    clean_text = text.strip()
    print(f"\n🤖 JARVIS: \"{clean_text}\"")

    with tempfile.NamedTemporaryFile(suffix="_jarvis.mp3", delete=False) as tf:
        temp_audio_path = tf.name

    try:
        success = asyncio.run(_generate_edge_speech(clean_text, temp_audio_path, voice))
        if success:
            play_audio(temp_audio_path)
            return
    except Exception as e:
        print(f"[TTS Fallback]: {e}")
    finally:
        if os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except Exception:
                pass

    # Fallback: pyttsx3
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(clean_text)
        engine.runAndWait()
    except Exception:
        pass
