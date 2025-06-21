from typing import TypedDict
from langgraph.graph import MessagesState
from src.mock.customer import Customer

class AgentBranding(TypedDict):
  name: str
  persona: str
  tone: str

class State(MessagesState):
  conversation_channel: str
  welcome_message: str
  otp_sent: bool
  customer: Customer
  agent_branding: AgentBranding