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
from langchain_mistralai import ChatMistralAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import ToolMessage, AIMessage, SystemMessage
import json
from src.verticals.provider.prompts import agent_prompt


class Configuration(TypedDict):
    """Configurable parameters for the agent.

    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    model_name: str
    recursion_limit: int
    thread_id: int


tools = [
    welcome_message,
    list_appointments,
    book_appointment,
    confirm_appointment,
    cancel_appointment,
]

tools_by_name = {tool.name: tool for tool in tools}


def agent_node(state: State, config: RunnableConfig):
    system_prompt = agent_prompt(state)

    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    # llm = ChatMistralAI(
    #     model_name="mistral-large-latest",
    #     temperature=0.0,
    # ).bind_tools(tools)

    llm = ChatAnthropic(
        model_name="claude-3-5-haiku-latest",
        temperature=0.0,
        max_retries=2,
        timeout=10,
        stop=None,
    ).bind_tools(tools)

    response = llm.invoke(messages)

    return {"messages": [response]}


def tool_node(state: State):
    outputs = []

    last_message = state["messages"][-1]

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
    messages = state["messages"]

    last_message = messages[-1]

    # If there is no function call, then we finish
    if isinstance(last_message, AIMessage) and not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"


def build_agent():

    agent_builder = StateGraph(State, Configuration)

    agent_builder.add_node("agent", agent_node)
    agent_builder.add_node("tools", ToolNode(tools))

    agent_builder.add_edge(START, "agent")
    agent_builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        },
    )
    agent_builder.add_edge("tools", "agent")

    return agent_builder.compile(name="appointment_agent")


appointment_agent = build_agent()
