import pyaudio

print("=" * 60)
print("       Audio Input Device Scanner")
print("=" * 60)

try:
    p = pyaudio.PyAudio()
except Exception as e:
    print(f"❌ Could not initialize PyAudio: {e}")
    exit(1)

count = p.get_device_count()
print(f"Total audio devices reported by PortAudio: {count}\n")

# Try default input device info
try:
    default_info = p.get_default_input_device_info()
    print(f"Default Input Device: ID {default_info['index']} -> '{default_info['name']}'\n")
except Exception as e:
    print(f"Default Input Device query failed: {e}\n")

input_devices = []
for i in range(count):
    try:
        info = p.get_device_info_by_index(i)
        max_in = info.get("maxInputChannels", 0)
        name = info.get("name", "")
        rate = int(info.get("defaultSampleRate", 44100))
        if max_in > 0:
            print(f"🎤 [Index {i}] {name} (Channels: {max_in}, Rate: {rate})")
            # Test stream
            try:
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=rate,
                    input=True,
                    input_device_index=i,
                    frames_per_buffer=1024
                )
                stream.close()
                input_devices.append((i, name, rate))
                print(f"     Status: READY TO RECORD ✅")
            except Exception as stream_err:
                print(f"     Status: Open failed ({stream_err}) ❌")
    except Exception as e:
        print(f"  Error reading device {i}: {e}")

p.terminate()

print("\n" + "=" * 60)
if input_devices:
    print(f"Found {len(input_devices)} working microphone device(s)!")
    print(f"Recommended Index for JARVIS: {input_devices[0][0]} ('{input_devices[0][1]}')")
else:
    print("❌ No working input devices found by PortAudio.")
print("=" * 60)

