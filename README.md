# ⚡ F.R.I.D.A.Y. - Autonomous AI Personal Assistant

An advanced, lightweight, and extensible autonomous AI agent capable of real-time voice conversation, social media automation, desktop control, and web agent capabilities.

---

## 🌟 Key Features

1. **🧠 Autonomous Decision Engine (Brain)**:
   - Powered by **Google Gemini 3.5 Flash** with native **Automatic Function Calling (AFC)**.
   - Automatically understands intent in both **Bengali and English** and triggers appropriate tools.

2. **🎙️ Natural Neural Voice Engine**:
   - **Edge-TTS**: Human-like crystal clear voices (`en-US-ChristopherNeural` & `bn-BD-PradeepNeural`).
   - Dynamic language switching (speaks Bengali when asked in Bengali, English when asked in English).

3. **🔌 Modular Plugin Architecture**:
   - **WhatsApp Web Plugin** (`plugins/whatsapp_plugin.py`): Check unread messages, read recent chat senders, and send WhatsApp messages.
   - **Telegram Plugin** (`plugins/telegram_plugin.py`): Read last incoming Telegram messages and send replies.
   - **Social Media Plugin** (`plugins/social_plugin.py`): Facebook & Instagram Messenger/DM check, and status posting.
   - **Gmail Plugin** (`plugins/mail_plugin.py`): Summarize unread emails and draft/send emails.
   - **OS & Software Manager** (`plugins/system_plugin.py`): Launch apps (Chrome, VS Code, Spotify, Terminal, Calculator), volume control, and CPU/RAM/Battery status.
   - **Web & ChatGPT Agent** (`plugins/web_agent_plugin.py`): Deep browser research, ChatGPT queries, and YouTube video playback.

4. **⚡ Ultra-Lightweight & Fast**:
   - No heavy 10GB local models consuming your RAM. Total memory footprint is `< 180 MB`.
   - Uses Playwright persistent profile (`~/.jarvis_browser_profile/`) to keep you logged into WhatsApp, Facebook, ChatGPT without re-authenticating every time.

---

## 📁 Project Architecture

```text
JARVIS-AI-Assistant/
├── config.py                 # API keys and credentials
├── main.py                   # Main autonomous service entry point
├── main_legacy.py            # Legacy backup
├── requirements.txt          # Dependencies
│
├── core/
│   ├── agent.py              # Stateful Gemini Agent with Automatic Function Calling
│   └── tool_registry.py      # Dynamic tool registration and schema generator
│
├── voice/
│   ├── listener.py           # Multi-language speech recognition (Bangla + English)
│   └── speaker.py            # Natural Neural Edge-TTS voice player
│
├── automation/
│   ├── browser_agent.py      # Playwright persistent session & ChatGPT automation
│   └── os_manager.py         # Application launcher, volume & system manager
│
└── plugins/                  # Extensible plugin folder
    ├── base.py               # Abstract Base Plugin
    ├── system_plugin.py      # OS, apps, volume, battery
    ├── web_agent_plugin.py   # ChatGPT, YouTube, web search
    ├── whatsapp_plugin.py    # WhatsApp Web read/send
    ├── telegram_plugin.py    # Telegram chat reader and sender
    ├── social_plugin.py      # Facebook & Instagram management
    └── mail_plugin.py        # Gmail check & drafting
```

---

## 🚀 Quick Start

### 1. Activate Virtual Environment
```bash
source ./venv/bin/activate
```

### 2. Configure API Keys in `config.py`
Open `config.py` and ensure your Gemini API key is set:
```python
gemini_api_key = "YOUR_GEMINI_API_KEY"
```

*(Optional for automated personal account reading)*:
- Telegram: `telegram_api_id` and `telegram_api_hash`
- Gmail: `gmail_address` and `gmail_app_password`

### 3. Run JARVIS
```bash
./venv/bin/python main.py
```

---

## 🗣️ Example Voice Commands

| Category | Example Command (Bangla / English) | What JARVIS Does |
| :--- | :--- | :--- |
| **System** | *"আমার পিসির ব্যাটারি আর র‍্যাম কেমন আছে?"* | Checks system stats and tells you via voice. |
| **App Launch** | *"জারভিস, ভিএস কোড ওপেন করো"* | Instantly launches VS Code. |
| **WhatsApp** | *"আমার হোয়াটসঅ্যাপে শেষ কে মেসেজ দিছে?"* | Checks WhatsApp Web and speaks the sender and message. |
| **WhatsApp Send** | *"রাকিবকে হোয়াটসঅ্যাপে মেসেজ দাও যে আমি আসছি"* | Types and sends the message to Rakib. |
| **ChatGPT** | *"চ্যাটজিপিটি ওপেন করে কোয়ান্টাম কম্পিউটিং নিয়ে তথ্য দাও"* | Automates ChatGPT and returns summary. |
| **YouTube** | *"ইউটিউবে একটা রিল্যাক্সিং গান প্লে করো"* | Finds and plays top song on YouTube. |
| **Social** | *"আমার ফেসবুকে একটা পোস্ট করে দাও: 'Hello world!'"* | Posts status update on Facebook. |
