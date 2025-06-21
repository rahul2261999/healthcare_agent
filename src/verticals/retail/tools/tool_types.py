from typing import Literal, TypedDict
from core.tools.tool_types import ToolDefinition

GET_ORDERS = 'get_orders'

ALL_TOOL_NAMES = [
    GET_ORDERS,
]

ToolName = Literal[
    'get_orders',
]

class RetailToolsJson(TypedDict):
  get_orders: ToolDefinition