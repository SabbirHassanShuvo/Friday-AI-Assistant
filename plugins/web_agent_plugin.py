import urllib.request
import urllib.parse
import json
from plugins.base import BasePlugin
from core.tool_registry import tool
from automation.browser_agent import browser

class WebAgentPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "web_agent_plugin"

    @property
    def description(self) -> str:
        return "Executes browser actions like querying ChatGPT, searching YouTube, and scraping web answers."

    def register_tools(self):
        @tool(name="ask_chatgpt", description="Opens ChatGPT in the browser, searches or submits user prompt, and extracts answer.")
        def ask_chatgpt(prompt: str) -> str:
            print(f"\n[Browser Agent]: Querying ChatGPT with '{prompt}'...")
            return browser.query_chatgpt(prompt)

        @tool(name="play_youtube_video", description="Searches YouTube for a song or video topic and plays the top result.")
        def play_youtube_video(video_query: str) -> str:
            print(f"\n[Browser Agent]: Playing '{video_query}' on YouTube...")
            return browser.search_youtube(video_query)

        @tool(name="search_web_data", description="Searches the web for latest facts, news, or general knowledge.")
        def search_web_data(query: str) -> str:
            # DuckDuckGo Instant Answer API (ultra-fast, zero api key required)
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    abstract = data.get("AbstractText", "")
                    if abstract:
                        return abstract
                    related = data.get("RelatedTopics", [])
                    if related and "Text" in related[0]:
                        return related[0]["Text"]
                    return f"Search completed for '{query}'. More details can be viewed by opening browser tab."
            except Exception as e:
                return f"Search error: {e}"

# Auto-instantiate and register tools
web_plugin = WebAgentPlugin()
web_plugin.register_tools()
