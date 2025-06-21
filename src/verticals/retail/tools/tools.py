from typing import Annotated
from langchain_core.tools import tool
from agent.state import MainState
from langgraph.prebuilt import InjectedState
from langchain_core.tools import InjectedToolCallId
from mock.retail import retailStore
from langgraph.types import Command
from langchain_core.messages import ToolMessage
import json

@tool('get_orders', 
  description="""It is used to get all the orders of the customer"""
)
def get_orders(
  state: Annotated[MainState, InjectedState], 
  tool_call_id: Annotated[str, InjectedToolCallId]
):
  customer_id = state['customer_id']
  
  if customer_id is None or customer_id == "":
    return Command(
        update={
          "messages": state['messages'] + [
              ToolMessage(content="Customer ID is required to get orders", tool_call_id=tool_call_id)
          ]
        }
    )
  
  orders = retailStore.get_orders(customer_id=customer_id)
  
  return Command(
    update={
      "messages": state['messages'] + [
        ToolMessage(content=json.dumps(orders), tool_call_id=tool_call_id)
      ]
    }
  )