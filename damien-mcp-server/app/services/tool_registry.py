# Placeholder for tool registration
import logging
from typing import Callable, Dict, Any

logger = logging.getLogger(__name__)

class ToolDefinition:
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any], handler: str, requires_scopes: list = None, rate_limit_group: str = None, confirmation_required: bool = False):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.handler_name = handler # Storing handler name, actual function resolved elsewhere
        self.requires_scopes = requires_scopes or []
        self.rate_limit_group = rate_limit_group
        self.confirmation_required = confirmation_required

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable] = {}

    def register_tool(self, tool_def: ToolDefinition, handler_func: Callable):
        if tool_def.name in self._tools:
            logger.warning(f"Tool '{tool_def.name}' is already registered. Overwriting.")
        self._tools[tool_def.name] = tool_def
        self._handlers[tool_def.handler_name] = handler_func # Store handler by its name string
        logger.info(f"Registered tool: {tool_def.name} with handler {tool_def.handler_name}")

    def get_tool_definition(self, tool_name: str) -> ToolDefinition | None:
        return self._tools.get(tool_name)

    def get_handler(self, handler_name: str) -> Callable | None:
        return self._handlers.get(handler_name)

    def get_all_tools(self) -> Dict[str, ToolDefinition]:
        return self._tools.copy()

# Singleton instance
tool_registry = ToolRegistry()