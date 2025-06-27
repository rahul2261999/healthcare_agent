from typing import TypedDict, Callable

class ToolDefinition(TypedDict):
    description: str
    tool: Callable

