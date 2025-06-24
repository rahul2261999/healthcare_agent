from typing import Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from src.mock.customer import Customer
from pydantic import BaseModel

class AgentBranding(BaseModel):
  name: str
  persona: str
  tone: str

class State(BaseModel):
  messages: Annotated[list[AnyMessage], add_messages]
  conversation_channel: str
  welcome_message: str
  otp_sent: bool
  customer: Customer
  agent_branding: AgentBranding