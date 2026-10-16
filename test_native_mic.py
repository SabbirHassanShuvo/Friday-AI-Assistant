import os
import subprocess
import speech_recognition as sr
from voice import speak

print("=" * 60)
print("     Ubuntu PulseAudio / Native Recording Test")
print("=" * 60)

temp_wav = "/tmp/test_jarvis_mic.wav"
if os.path.exists(temp_wav):
    os.remove(temp_wav)

duration = 4
print(f"\n🎙️  RECORDING FOR {duration} SECONDS FROM FRONT MICROPHONE...")
print(">>> Speak NOW (e.g., 'Hello Jarvis what is the time') <<<")

# Method 1: ffmpeg via pulse (connects to the exact device in Ubuntu Settings)
recorded = False

# Try ffmpeg pulse
cmd_ffmpeg = [
    "ffmpeg", "-y", "-loglevel", "quiet",
    "-f", "pulse", "-i", "default",
    "-t", str(duration),
    "-ar", "16000", "-ac", "1",
    temp_wav
]

# Try arecord fallback
cmd_arecord = [
    "arecord", "-q",
    "-f", "S16_LE", "-r", "16000", "-c", "1",
    "-d", str(duration),
    temp_wav
]

for cmd in [cmd_ffmpeg, cmd_arecord]:
    try:
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(temp_wav) and os.path.getsize(temp_wav) > 1000:
            recorded = True
            print("✅ Audio recorded successfully!")
            break
    except Exception as e:
        continue

if not recorded:
    print("❌ Recording failed with system tools.")
    exit(1)

# Playback recorded voice to verify it heard you
print("\n🔊 Playing back what was recorded from your microphone...")
subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", temp_wav],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Speech recognition
print("\n⏳ Recognizing speech with Google Speech Recognition...")
recognizer = sr.Recognizer()

try:
    with sr.AudioFile(temp_wav) as source:
        audio = recognizer.record(source)

    recognized = False
    for lang in ["en-US", "en-IN", "bn-BD"]:
        try:
            text = recognizer.recognize_google(audio, language=lang)
            print(f"\n🎉 SUCCESS ({lang})! You said: \"{text}\"")
            speak(f"Sir, I heard you say: {text}")
            recognized = True
            break
        except sr.UnknownValueError:
            continue

    if not recognized:
        print("\n❓ Google could not understand the speech. Did you hear your own voice during playback?")

except Exception as e:
    print(f"❌ Recognition Error: {e}")

print("=" * 60)

