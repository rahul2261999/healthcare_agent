from typing import TypedDict
from src.core.prebuilt.tools.tool_types import ToolDefinition
from enum import Enum

class ToolName(str, Enum):
    WELCOME_MESSAGE = 'welcome_message'
    LIST_APPOINTMENTS = 'list_appointments'
    BOOK_APPOINTMENT = 'book_appointment'
    CONFIRM_APPOINTMENT = 'confirm_appointment'
    CANCEL_APPOINTMENT = 'cancel_appointment'
    RESCHEDULE_APPOINTMENT = 'reschedule_appointment'

class ProviderToolsJson(TypedDict):
    welcome_message: ToolDefinition
    get_appointments: ToolDefinition
    book_appointment: ToolDefinition
    confirm_appointment: ToolDefinition
    cancel_appointment: ToolDefinition
    reschedule_appointment: ToolDefinition
    
class RetailToolsJson(TypedDict):
    get_orders: ToolDefinition
