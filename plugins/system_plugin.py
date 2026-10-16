from plugins.base import BasePlugin
from core.tool_registry import tool
from automation.os_manager import open_application, open_url_tab, get_system_status, set_system_volume
import datetime

class SystemPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "system_plugin"

    @property
    def description(self) -> str:
        return "Controls OS operations, software launching, volume, time, and system health."

    def register_tools(self):
        @tool(name="open_app", description="Opens software application like Chrome, VS Code, Terminal, Spotify, Calculator.")
        def open_app(app_name: str) -> str:
            return open_application(app_name)

        @tool(name="open_browser_tab", description="Opens a website or tab in the browser, e.g. youtube.com, github.com.")
        def open_browser_tab(url: str) -> str:
            return open_url_tab(url)

        @tool(name="check_system_health", description="Gets CPU, RAM, and Battery percentage of the computer.")
        def check_system_health() -> str:
            status = get_system_status()
            return f"Time: {status['time']}, CPU: {status['cpu_usage']}, RAM: {status['ram_usage']}, Battery: {status['battery']}"

        @tool(name="control_volume", description="Adjusts system audio volume: 'up', 'down', 'mute'.")
        def control_volume(action: str) -> str:
            return set_system_volume(action)

        @tool(name="get_current_time_date", description="Returns the current time, date, and day.")
        def get_current_time_date() -> str:
            now = datetime.datetime.now()
            return now.strftime("Current time is %I:%M %p, and today is %A, %B %d, %Y.")

# Auto-instantiate and register tools
system_plugin = SystemPlugin()
system_plugin.register_tools()
