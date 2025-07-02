from typing import TypedDict
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import ToolNode
from src.agents.state import State
from src.verticals.provider.tools import (
    welcome_message,
    list_appointments,
    book_appointment,
    confirm_appointment,
    cancel_appointment,
)
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage, AIMessage, SystemMessage
import json
from src.verticals.provider.prompts import agent_prompt
from src.verticals.authentication import send_otp, verify_otp
from langgraph.checkpoint.memory import MemorySaver
from src.lib.logger import logger
from src.core.prebuilt.types.llm_provider import LLMProvider, LLMModel

class Configuration(TypedDict):
    """Configurable parameters for the agent.

    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    recursion_limit: int
    thread_id: str


appointment_tools = [
    welcome_message,
    list_appointments,
    book_appointment,
    confirm_appointment,
    cancel_appointment,
]

authentication_tools = [
    send_otp,
    verify_otp,
]

tools = appointment_tools + authentication_tools

tools_by_name = {tool.name: tool for tool in tools}


def appointment_node(state: State, config: RunnableConfig):
    system_prompt = agent_prompt(state)

    messages = [SystemMessage(content=system_prompt)] + state.messages

    llm = init_chat_model(
        model=LLMModel.CLAUDE_3_HAIKU_20240307.value,
        model_provider=LLMProvider.ANTHROPIC.value,
        temperature=0.0,
        max_retries=2,
        timeout=10,
    ).bind_tools(tools)

    response = llm.invoke(messages)

    return {"messages": [response], "active_node": "appointment_node"}


def tool_node(state: State):
    outputs = []

    last_message = state.messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        print(f"Tool calls: {last_message.tool_calls}")

        for tool_call in last_message.tool_calls:
            print(f"Tool call: {tool_call}")

            tool_result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
            print(f"Tool result: {tool_result}")

            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )

    return {"messages": outputs}


# Define the conditional edge that determines whether to continue or not
def should_continue(state: State):
    messages = state.messages

    last_message = messages[-1]

    # If there is no function call, then we finish
    if isinstance(last_message, AIMessage) and not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"


def build_agent(add_checkpoint: bool = False):
    agent_builder = StateGraph(State, config_schema=Configuration)

    agent_builder.add_node("appointment_node", appointment_node)
    agent_builder.add_node("tools", ToolNode(tools))

    agent_builder.add_edge(START, "appointment_node")

    agent_builder.add_conditional_edges(
        "appointment_node",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        },
    )

    agent_builder.add_edge("tools", "appointment_node")

    if add_checkpoint:
        logger.info("Compiling with checkpoint")
        return agent_builder.compile(name="provider_agent", checkpointer=checkpointer)
    else:
        return agent_builder.compile(name="provider_agent")


checkpointer = MemorySaver()
appointment_agent = build_agent(add_checkpoint=True)
langgraph_agent = build_agent(add_checkpoint=False)
