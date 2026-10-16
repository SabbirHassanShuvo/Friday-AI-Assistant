import inspect
import json
from typing import Callable, Dict, Any, List

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str = None, description: str = None):
        """Decorator to register a function as an agent tool."""
        def decorator(func: Callable):
            tool_name = name or func.__name__
            doc = description or inspect.getdoc(func) or "No description provided."
            
            sig = inspect.signature(func)
            parameters = {
                "type": "OBJECT",
                "properties": {},
                "required": []
            }

            for param_name, param in sig.parameters.items():
                if param_name in ("self", "cls"):
                    continue
                param_type = "STRING"
                if param.annotation == int:
                    param_type = "INTEGER"
                elif param.annotation == bool:
                    param_type = "BOOLEAN"
                elif param.annotation == float:
                    param_type = "NUMBER"

                parameters["properties"][param_name] = {
                    "type": param_type,
                    "description": f"Parameter: {param_name}"
                }
                if param.default == inspect.Parameter.empty:
                    parameters["required"].append(param_name)

            self._tools[tool_name] = {
                "func": func,
                "name": tool_name,
                "description": doc,
                "parameters": parameters
            }
            return func
        return decorator

    def get_all_tools(self) -> List[Callable]:
        """Returns list of all callable tool functions."""
        return [t["func"] for t in self._tools.values()]

    def get_gemini_tool_declarations(self) -> List[Dict[str, Any]]:
        """Returns tool declarations formatted for Gemini REST / direct API."""
        decls = []
        for t in self._tools.values():
            decls.append({
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"]
            })
        return decls

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Executes a tool by name with provided arguments and returns string result."""
        if tool_name not in self._tools:
            return f"Error: Tool '{tool_name}' is not registered."
        
        func = self._tools[tool_name]["func"]
        try:
            res = func(**args)
            if isinstance(res, (dict, list)):
                return json.dumps(res, ensure_ascii=False)
            return str(res)
        except Exception as e:
            return f"Error executing '{tool_name}': {str(e)}"

# Global Tool Registry instance
registry = ToolRegistry()
tool = registry.register
