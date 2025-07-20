from typing import Annotated, Optional

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

METADATA_KEY_HANDOFF_DESTINATION = "__handoff_destination"

def create_handoff_tool(
  *, 
  agent_name: str, 
  name: str | None = None, 
  description: str | None = None,
  include_state_keys: Optional[list[str]] = None,
  return_direct: bool = False
) -> BaseTool:
  """Create a tool that can handoff control to the requested agent.

  Args:
      agent_name: The name of the agent to handoff control to, i.e.
        the name of the agent node in the multi-agent graph.
        Agent names should be simple, clear and unique, preferably in snake_case,
        although you are only limited to the names accepted by LangGraph
        nodes as well as the tool names accepted by LLM providers
        (the tool name will look like this: `transfer_to_<agent_name>`).
      name: Optional name of the tool to use for the handoff.
        If not provided, the tool name will be `transfer_to_<agent_name>`.
      description: Optional description for the handoff tool.
        If not provided, the tool description will be `Ask agent <agent_name> for help`.
  """
  if name is None:
    name = f"transfer_to_{agent_name}"

  if description is None:
    description = f"Ask agent '{agent_name}' for help"
      
  include_state_keys = include_state_keys or []

  @tool(name, description=description, return_direct=return_direct)
  def handoff_to_agent(
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
  ):
    tool_message = ToolMessage(
      content=f"Successfully transferred to {agent_name}",
      name=name,
      tool_call_id=tool_call_id,
    )
    
    additional_state_data = {
      key: state[key] for key in include_state_keys if key in state
    }
    
    return Command(
      goto=agent_name,
      graph=Command.PARENT,
      update={
        "messages": state["messages"] + [tool_message], 
        "active_agent": agent_name,
        **additional_state_data
      },
    )

  handoff_to_agent.metadata = {METADATA_KEY_HANDOFF_DESTINATION: agent_name}
  
  return handoff_to_agent

