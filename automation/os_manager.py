import os
import sys
import subprocess
import shutil
import webbrowser
import psutil
import datetime

# Common App Aliases for Linux & Windows
APP_COMMANDS = {
    "chrome": ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"],
    "browser": ["google-chrome", "firefox", "chromium"],
    "firefox": ["firefox"],
    "vscode": ["code"],
    "terminal": ["gnome-terminal", "x-terminal-emulator", "konsole", "alacritty", "xfce4-terminal"],
    "files": ["nautilus", "dolphin", "thunar", "xdg-open ."],
    "calculator": ["gnome-calculator", "kcalc", "calc"],
    "settings": ["gnome-control-center"],
    "spotify": ["spotify"],
    "vlc": ["vlc"],
    "notepad": ["gedit", "kate", "notepad"]
}

def open_application(app_name: str) -> str:
    """Launches an installed software application by name or alias."""
    app_key = app_name.lower().strip()
    
    # 1. Check known aliases
    candidates = APP_COMMANDS.get(app_key, [app_key])
    for cmd in candidates:
        full_path = shutil.which(cmd)
        if full_path:
            try:
                subprocess.Popen([full_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Successfully opened {app_name}."
            except Exception as e:
                return f"Failed to start {app_name}: {e}"

    # 2. Try generic xdg-open / start
    try:
        if sys.platform.startswith("win"):
            os.startfile(app_name)
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", "-a", app_name])
        else:
            # Linux: try app_name directly or desktop file
            subprocess.Popen([app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Attempted to open {app_name}."
    except Exception as e:
        return f"Could not find or launch application '{app_name}'. Error: {e}"

def open_url_tab(url: str) -> str:
    """Opens a website or tab directly in the user's primary Google Chrome (with login sessions)."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    # Prioritize user's real installed Google Chrome with existing profile
    chrome_cmd = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    if chrome_cmd:
        try:
            subprocess.Popen([chrome_cmd, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Opened {url} in your primary Google Chrome."
        except Exception:
            pass

    # Fallback to xdg-open / webbrowser
    try:
        webbrowser.open_new_tab(url)
        return f"Opened tab: {url}"
    except Exception as e:
        return f"Could not open browser tab: {e}"

def get_system_status() -> dict:
    """Returns current system health: CPU, RAM, Battery, and Time."""
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%A, %B %d, %Y")
    
    cpu_percent = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    ram_percent = mem.percent
    
    battery = psutil.sensors_battery()
    bat_str = f"{battery.percent}% ({'Charging' if battery.power_plugged else 'Discharging'})" if battery else "Not available (Desktop/AC power)"

    return {
        "time": time_str,
        "date": date_str,
        "cpu_usage": f"{cpu_percent}%",
        "ram_usage": f"{ram_percent}%",
        "battery": bat_str
    }

def set_system_volume(action: str) -> str:
    """Controls system audio volume: 'up', 'down', 'mute', or 'unmute'."""
    action = action.lower().strip()
    try:
        if "up" in action:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"], check=True)
            return "Volume increased by 10%."
        elif "down" in action:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"], check=True)
            return "Volume decreased by 10%."
        elif "mute" in action:
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"], check=True)
            return "Volume mute toggled."
        return "Unknown volume action."
    except Exception as e:
        return f"Failed to adjust volume: {e}"
