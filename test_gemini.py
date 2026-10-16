import json
import urllib.request
import urllib.error
import config

print("=" * 60)
print("       Gemini Models & Compatibility Test")
print("=" * 60)

key = getattr(config, "gemini_api_key", "").strip()
print(f"Key loaded: {key[:8]}...{key[-6:]} (Length: {len(key)})")

# 1. Fetch available models for this key
list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
available_generate_models = []

try:
    with urllib.request.urlopen(list_url, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print("\nAvailable models on your account:")
        for m in data.get("models", []):
            name = m.get("name", "").replace("models/", "")
            methods = m.get("supportedGenerationMethods", [])
            if "generateContent" in methods:
                available_generate_models.append(name)
                print(f"  ✅ {name}")
except Exception as e:
    print(f"ListModels error: {e}")

# If list returned models, use the first fast flash model, otherwise try current models
candidate_models = available_generate_models if available_generate_models else [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-pro-preview",
    "gemini-flash-latest"
]

print(f"\nTesting generation with candidate models: {candidate_models[:3]}...")
success = False

for model in candidate_models:
    test_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": "Hello, answer in 5 words."}]}]
    }
    req = urllib.request.Request(
        test_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": key}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            reply = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            print(f"\n🎉 SUCCESS WITH MODEL '{model}'!")
            print(f"JARVIS reply: \"{reply}\"")
            success = True
            break
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            msg = json.loads(err_body).get("error", {}).get("message", str(e))
        except Exception:
            msg = err_body
        print(f"  ❌ Model '{model}' failed: {msg[:80]}...")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("=" * 60)
