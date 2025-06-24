from typing import Annotated
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
import json
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from src.agents.state import State
from langchain_core.tools import tool
from src.mock.provider import providerStore, Appointment, AppointmentStatus
import uuid
from .tool_types import ToolName
from src.utils.datetime import get_current_datetime_in_ist


@tool(
    ToolName.WELCOME_MESSAGE.value,
    description="""
   It is used to send the welcome message to the user.
   """,
)
def welcome_message(
    state: Annotated[State, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    welcome_message = (
        state.welcome_message
        or "Hello, I am your Ai assistant. I can help you with your appointment and order related queries."
    )
    tool_message = ToolMessage(content=welcome_message, tool_call_id=tool_call_id)

    return Command(update={"messages": state.messages + [tool_message]})  # type: ignore


@tool(
    ToolName.LIST_APPOINTMENTS.value,
    description="""It is used to list all the appointments of the customer""",
)
def list_appointments(
    state: Annotated[State, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    print(f"Looking up appointment for customer {state.customer.id}")
    customer_id = state.customer.id

    if customer_id is None or customer_id == "":
        return Command(
            update={
                "messages": state.messages
                + [
                    ToolMessage(
                        content="Customer ID is required to get appointments",
                        tool_call_id=tool_call_id,
                    )
                ]  # type: ignore
            }
        )

    appointments = providerStore.get_appointments(customer_id=customer_id)

    return Command(
        update={
            "messages": state.messages
            + [
                ToolMessage(
                    content=f"Here are the appointments: {json.dumps(appointments)}",
                    tool_call_id=tool_call_id,
                )
            ]  # type: ignore
        }
    )


@tool(
    ToolName.BOOK_APPOINTMENT.value,
    description=f"""
    Tool Description: Appointment Booking

      Books an appointment for the customer using a valid future date and time.
      ---
      Input Requirements
      - Date: Must be in `MM-DD-YYYY` format  
      - Time: Must be in `HH:MM` (24-hour format)
      ---
      Current Date and Time  
      (Current IST): `{get_current_datetime_in_ist()}`
      ---

      Parsing & Validation Rules
      1. Date must be today or a future date.  
      2. Time must be at least 10 minutes ahead of the current IST time.
      3. Only future appointments are allowed. No backdating.
      4. Relative expressions like `"tomorrow"` or `"next Sunday"` are allowed and will be resolved using the current IST datetime (`{get_current_datetime_in_ist()}`).
      5. The system will auto-resolve to the correct year, e.g., if today is June 6, 2025, then “next Sunday” is resolved as June 8, 2025.
      6. All times and dates are validated in India Standard Time (IST) only.

  """,
)
def book_appointment(
    date: str,
    time: str,
    state: Annotated[State, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
):

    print(f"Booking appointment for customer {state.customer.id}")
    customer_id = state.customer.id

    if customer_id is None or customer_id == "":
        return Command(
            update={
                "messages": state.messages
                + [
                    ToolMessage(
                        content="Customer ID is required to book appointment",
                        tool_call_id=tool_call_id,
                    )
                ]  # type: ignore
            }
        )

    appointment = Appointment(
        id=str(uuid.uuid4()),
        customer_id=customer_id,
        date=date,
        time=time,
        status=AppointmentStatus.PENDING,
    )

    providerStore.add_appointment(appointment=appointment)

    return Command(
        update={
            "messages": state.messages
            + [
                ToolMessage(
                    content=f"Appointment booked successfully for {date} at {time}",
                    tool_call_id=tool_call_id,
                )
            ]  # type: ignore
        }
    )


@tool(
    ToolName.CONFIRM_APPOINTMENT.value,
    description="""
  Confirms an appointment for the customer using a valid appointment id.
  List all the appointments for the customer if appointment id is not provided by the user.
  
  Input Requirements:
    - Appointment ID: Must be a valid appointment id.
    
  Parsing Rules:
    - Appointment ID must be a valid appointment id.
  """,
)
def confirm_appointment(
    appointment_id: str,
    state: Annotated[State, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    print(f"Confirming appointment for customer {state.customer.id}")
    customer_id = state.customer.id

    if customer_id is None or customer_id == "":
        return Command(
            update={
                "messages": state.messages
                + [
                    ToolMessage(
                        content="Customer ID is required to confirm appointment",
                        tool_call_id=tool_call_id,
                    )
                ]  # type: ignore
            }
        )

    appointment = providerStore.get_appointment(appointment_id=appointment_id)

    if appointment is None:
        return Command(
            update={
                "messages": state.messages + [ToolMessage(content=f"Appointment {appointment_id} not found", tool_call_id=tool_call_id)]  # type: ignore
            }
        )

    if appointment.status == AppointmentStatus.CONFIRMED:
        return Command(
            update={
                "messages": state.messages + [ToolMessage(content=f"Appointment {appointment_id} is already confirmed", tool_call_id=tool_call_id)]  # type: ignore
            }
        )

    if appointment.status == AppointmentStatus.COMPLETED:
        return Command(
            update={
                "messages": state.messages + [ToolMessage(content=f"Appointment {appointment_id} is already completed", tool_call_id=tool_call_id)]  # type: ignore
            }
        )

    providerStore.update_appointment(
        appointment_id=appointment_id, status=AppointmentStatus.CONFIRMED
    )

    return Command(
        update={
            "messages": state.messages + [ToolMessage(content=f"Appointment {appointment_id} confirmed successfully", tool_call_id=tool_call_id)]  # type: ignore
        }
    )


@tool(
    ToolName.CANCEL_APPOINTMENT.value,
    description="""
  Cancels an appointment for the customer using a valid appointment id.
  
  Input Requirements:
    - Appointment ID: Must be a valid appointment id.
    
  Parsing Rules:
    - Appointment ID must be a valid appointment id.
  """,
)
def cancel_appointment(
    appointment_id: str,
    state: Annotated[State, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    print(f"Cancelling appointment for customer {state.customer.id}")
    customer_id = state.customer.id

    if customer_id is None or customer_id == "":
        return Command(
            update={
                "messages": state.messages + [ToolMessage(content="Customer ID is required to cancel appointment", tool_call_id=tool_call_id)]  # type: ignore
            }
        )

    appointment = providerStore.get_appointment(appointment_id=appointment_id)

    if appointment is None:
        return Command(
            update={
                "messages": state.messages + [ToolMessage(content=f"Appointment {appointment_id} not found", tool_call_id=tool_call_id)]  # type: ignore
            }
        )

    if appointment.status == AppointmentStatus.COMPLETED:
        return Command(
            update={
                "messages": state.messages + [ToolMessage(content=f"Appointment {appointment_id} is already completed, cannot be cancelled", tool_call_id=tool_call_id)]  # type: ignore
            }
        )

    providerStore.update_appointment(
        appointment_id=appointment_id, status=AppointmentStatus.CANCELLED
    )

    return Command(
        update={
            "messages": state.messages + [ToolMessage(content=f"Appointment {appointment_id} cancelled successfully", tool_call_id=tool_call_id)]  # type: ignore
        }
    )
