from typing import TypedDict
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import ToolNode
from src.agents.state import State, IntentIdentificationResponse
from src.verticals.provider.tools import (
    welcome_message,
    list_appointments,
    book_appointment,
    confirm_appointment,
    cancel_appointment,
)
from langchain_openai import ChatOpenAI
from langchain_mistralai import ChatMistralAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import ToolMessage, AIMessage, SystemMessage
import json
from src.verticals.provider.prompts import agent_prompt
from src.verticals.authentication import authentication_prompt, send_otp, verify_otp
from langgraph.checkpoint.memory import MemorySaver
from src.verticals.intent_identification.prompt import intent_identification_prompt
from src.lib.logger import logger


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

    llm = ChatOpenAI(
        model="gpt-4o-mini",
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

checkpointer=MemorySaver()
appointment_agent = build_agent(add_checkpoint=True)
langgraph_agent = build_agent(add_checkpoint=False)
