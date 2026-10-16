from abc import ABC, abstractmethod

class BasePlugin(ABC):
    """Abstract Base Class for JARVIS plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the plugin."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this plugin handles."""
        pass

    @abstractmethod
    def register_tools(self):
        """Registers plugin tools with the central ToolRegistry."""
        pass
