from typing import Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from src.mock.customer import Customer
from pydantic import BaseModel

class AgentBranding(BaseModel):
  name: str
  persona: str
  tone: str

class AuthenticationState(BaseModel):
  is_authorized: bool
  otp_sent: bool

class State(BaseModel):
  active_node: str
  messages: Annotated[list[AnyMessage], add_messages]
  conversation_channel: str
  welcome_message: str
  customer: Customer
  agent_branding: AgentBranding
  authentication: AuthenticationState


class IntentIdentificationResponse(BaseModel):
  active_node: str
  thinking: str