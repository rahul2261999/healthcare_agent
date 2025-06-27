from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage, AIMessage
from src.agents.state import State
from langgraph.types import Command
from langgraph.prebuilt import InjectedState
from typing import Annotated, Union

MOCK_OTP = "123456"

@tool("send_otp", description="Send an OTP to the user")
def send_otp(state: Annotated[State, InjectedState], tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
    try:
        phone_number = state.customer.phone_number
        # In a real implementation, this would actually send an SMS
        print(f"Sending OTP: {MOCK_OTP} to phone number: {phone_number}")
        
        msg_list = list(state.messages)
        msg_list.append(ToolMessage(
            name="send_otp",
            content=f"OTP sent successfully to {phone_number}",
            tool_call_id=tool_call_id
        ))

        msg_list.append(AIMessage(content=f"OTP sent successfully to {phone_number}"))

        return Command(
            update={
                "messages": msg_list,
                "authentication": {
                    **state.authentication.model_dump(),
                    "otp_sent": True
                }
            },
        )
    
    except Exception as e:
        return Command(
            update={
                "messages": [f"Failed to send OTP: {str(e)}"],
                "otp_sent": False
            },
        )

@tool("verify_otp", description="Verify the OTP provided by the user")
def verify_otp(otp: str, state: Annotated[State, InjectedState], tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
    try:
        stored_otp = MOCK_OTP
        
        if not stored_otp:
            tool_message = ToolMessage(content="No OTP found for this phone number", tool_call_id=tool_call_id)
            return Command(
                update={
                    "messages": [tool_message]
                }
            )
        
        if stored_otp == otp:
            msg_list = list(state.messages)
            msg_list.append(ToolMessage(
                name="verify_otp",
                content="OTP verified successfully",
                tool_call_id=tool_call_id
            ))

            return Command(
                update={ 
                    "authentication": {
                        **state.authentication.model_dump(),
                        "is_authorized": True,
                    },
                    "messages": msg_list
                },
            )
        
        tool_message = ToolMessage(content="Invalid OTP, Please enter the correct OTP", tool_call_id=tool_call_id)
        
        return Command(
            update={
                "messages": [tool_message]
            }
        )
    
    except Exception as e:
        tool_message = ToolMessage(content=f"OTP verification failed: {str(e)}", tool_call_id=tool_call_id)
        
        return Command(
            update={
                "messages": [tool_message]
            }
        )


def validate_authorization(state: State, tool_call_id: str) -> tuple[bool, Union[None, Command]]:
    if  not state.authentication.is_authorized:

        msg_list = list(state.messages)
        msg_list.append(ToolMessage(
            name="validate_authorization",
            content="You are not authorized to use this service, authenticating the user",
            tool_call_id=tool_call_id
        ))

        return False, Command(
            update={
                "active_node": "auth_node",
                "messages": msg_list
            }
        )


    return True, None
    