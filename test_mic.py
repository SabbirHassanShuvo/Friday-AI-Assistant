import sys
import speech_recognition as sr
import pyaudio
from voice import speak

print("=" * 60)
print("       JARVIS Microphone & Audio Device Diagnostic")
print("=" * 60)

p = pyaudio.PyAudio()
device_count = p.get_device_count()
print(f"\nTotal audio devices detected by system: {device_count}")

input_devices = []
for i in range(device_count):
    try:
        info = p.get_device_info_by_index(i)
        max_in = info.get("maxInputChannels", 0)
        name = info.get("name", "Unknown")
        host_api = info.get("hostApi", 0)
        if max_in > 0:
            input_devices.append((i, name, max_in))
            print(f"  [Input Device ID {i}] {name} (Channels: {max_in})")
        else:
            print(f"  [Output-only ID {i}] {name}")
    except Exception as e:
        print(f"  [Error ID {i}]: {e}")

p.terminate()

if not input_devices:
    print("\n" + "!" * 60)
    print("❌ কোন মাইক্রোফোন ইনপুট পাওয়া যায়নি! (No Input Device Found)")
    print("!" * 60)
    print("সম্ভাব্য কারণ ও সমাধান:")
    print(" 1. এটি একটি ডেস্কটপ কম্পিউটার (MSI মাদারবোর্ড)। ডেস্কটপে ইন-বিল্ট মাইক থাকে না।")
    print("    আপনার হেডফোন/হেডসেট বা ওয়েবক্যামের মাইক্রোফোন জ্যাক পিসিতে প্লাগ-ইন করুন।")
    print(" 2. যদি হেডফোন লাগানো থাকে, তবে সেটি 'Front Mic' নাকি 'Rear Mic' পোর্টে লাগানো চেক করুন।")
    print(" 3. Ubuntu Settings -> Sound -> Input-এ গিয়ে নিশ্চিত করুন মাইক্রোফোন শো করছে কি না।")
    print("=" * 60)
    sys.exit(1)

# Pick best candidate device
selected_device = None
for idx, name, ch in input_devices:
    if "pulse" in name.lower() or "default" in name.lower():
        selected_device = idx
        break
if selected_device is None:
    selected_device = input_devices[0][0]

print(f"\n✅ Testing Input Device [ID {selected_device}]: {dict((i, n) for i, n, _ in input_devices)[selected_device]}")

r = sr.Recognizer()
r.energy_threshold = 300
r.pause_threshold = 0.8

try:
    with sr.Microphone(device_index=selected_device) as source:
        print("Calibrating background noise (stay quiet for 1 sec)...")
        r.adjust_for_ambient_noise(source, duration=1.0)
        print(f"Energy threshold set to: {r.energy_threshold:.1f}")

        print("\n>>> PLEASE SPEAK SOMETHING NOW (e.g. 'Hello Jarvis') <<<")
        audio = r.listen(source, timeout=6, phrase_time_limit=8)
        print("Audio recorded! Now recognizing with Google Speech...")

        recognized = False
        for lang in ["en-US", "en-IN", "bn-BD"]:
            try:
                text = r.recognize_google(audio, language=lang)
                print(f"\n🎉 SUCCESS! ({lang}): You said: \"{text}\"")
                speak(f"I heard you say: {text}")
                recognized = True
                break
            except sr.UnknownValueError:
                continue

        if not recognized:
            print("\nCould not recognize voice. Please increase mic volume in Ubuntu Settings.")

except Exception as e:
    print(f"\n❌ Error with device {selected_device}: {e}")

print("=" * 60)
