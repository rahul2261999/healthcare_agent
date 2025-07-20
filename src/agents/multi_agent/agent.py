from typing import Literal, TypedDict
from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import ToolNode
from core.prebuilt.types.llm_provider import LLMModel, LLMProvider
from src.agents.state import State, IntentIdentificationResponse
from src.verticals.provider.tools import (
    welcome_message,
    list_appointments,
    book_appointment,
    confirm_appointment,
    cancel_appointment,
)
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import ToolMessage, AIMessage, SystemMessage
from src.verticals.provider.prompts import agent_prompt
from src.verticals.authentication import authentication_prompt, send_otp, verify_otp
from langgraph.checkpoint.memory import MemorySaver
from src.verticals.intent_identification.prompt import intent_identification_prompt
from src.lib.logger import logger
from langgraph.types import Command
from langgraph.prebuilt import InjectedState
from typing import Annotated
from langchain_core.tools import InjectedToolCallId, tool


class Configuration(TypedDict):
    """Configurable parameters for the agent.

    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    recursion_limit: int
    thread_id: str


@tool(
    "transfer_to_appointment_node",
    description="transfer to appointment_node for appointment related queries",
    return_direct=True,
)
def transfer_to_appointment_agent(
    state: Annotated[State, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command[Literal["appointment_agent"]]:
    tool_message = ToolMessage(
        content="Successfully transferred to appointment_agent",
        name="transfer_to_appointment_agent",
        tool_call_id=tool_call_id,
    )

    return Command(
        goto="appointment_agent",
        graph=Command.PARENT,
        update={
            "messages": state.messages + [tool_message],
        },
    )
    
@tool(
    "transfer_to_auth_agent",
    description="transfer to auth_agent for user authentication/authorization",
    return_direct=True,
)
def transfer_to_auth_agent(
    state: Annotated[State, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command[Literal["auth_agent"]]:
    tool_message = ToolMessage(
        content="Successfully transferred to auth_agent",
        name="transfer_to_auth_agent",
        tool_call_id=tool_call_id,
    )

    transfer_to_auth_agent.metadata = {"__handoff_destination": "auth_agent"}

    return Command(
        goto="auth_agent",
        graph=Command.PARENT,
        update={
            "messages": state.messages + [tool_message],
        },
    )



appointment_tools = [
    welcome_message,
    list_appointments,
    book_appointment,
    confirm_appointment,
    cancel_appointment,
    transfer_to_auth_agent,
]

authentication_tools = [
    send_otp,
    verify_otp,
    transfer_to_appointment_agent,
]


tools = appointment_tools + authentication_tools



def intent_identification_node(state: State):
    system_prompt = intent_identification_prompt(state)
    messages = [SystemMessage(content=system_prompt)] + state.messages

    llm = ChatAnthropic(
        model_name="claude-sonnet-4-20250514",
        temperature=0.0,
        max_retries=2,
        timeout=10,
        stop=None,
    )

    response = llm.with_structured_output(IntentIdentificationResponse).invoke(messages)

    parsed_response = IntentIdentificationResponse.model_validate(response)

    logger.info(f"Intent identification: {parsed_response.active_node}")
    logger.debug(f"Intent identification thinking: {parsed_response.thinking}")

    if parsed_response.active_node is None or parsed_response.active_node == "":
        return {"active_node": state.active_node}

    return {"active_node": parsed_response.active_node}


def appointment_node(state: State, config: RunnableConfig):
    system_prompt = agent_prompt(state)

    messages = [SystemMessage(content=system_prompt)] + state.messages


    messages = [
        message
        for message in messages
        if message.name != "transfer_to_auth_node"
        if not (isinstance(message, AIMessage) and len(message.tool_calls) > 0 and message.tool_calls[0]["name"] == "transfer_to_auth_node")
    ]

    llm = init_chat_model(
        model=LLMModel.GPT_4O_MINI.value,
        model_provider=LLMProvider.OPENAI.value,
        temperature=0.0,
        max_retries=2,
        timeout=10,
    ).bind_tools(appointment_tools)

    response = llm.invoke(messages)

    # remove the transfer_to_auth_node tool message

    return {"messages": [response]}


def authentication_node(state: State):
    system_prompt = authentication_prompt(state)

    messages = [SystemMessage(content=system_prompt)] + state.messages
   
    llm = init_chat_model(
        model=LLMModel.GPT_4O_MINI.value,
        model_provider=LLMProvider.OPENAI.value,
        temperature=0.0,
        max_retries=2,
        timeout=10,
    ).bind_tools(authentication_tools)

    response = llm.invoke(messages)

    # remove the transfer_to_appointment_node tool message
    messages = [
        message
        for message in messages
        if message.name != "transfer_to_appointment_node"
    ]

    return {"messages": [response]}


def is_authenticate(state: State):
    if state.authentication.is_authorized:
        return "yes"
    else:
        return "no"

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
    appointment_agent_builder = StateGraph(State, config_schema=Configuration)
    appointment_agent_builder.add_node("appointment_node", appointment_node)
    appointment_agent_builder.add_node("appointment_tools", ToolNode(appointment_tools))
    appointment_agent_builder.add_edge(START, "appointment_node")
    appointment_agent_builder.add_conditional_edges(
        "appointment_node",
        should_continue,    
        {
            "continue": "appointment_tools",
            "end": END,
        },
    )
    appointment_agent_builder.add_edge("appointment_tools", "appointment_node")

    if add_checkpoint:
        appointment_agent = appointment_agent_builder.compile(name="appointment_agent", checkpointer=MemorySaver())
    else:
        appointment_agent = appointment_agent_builder.compile(name="appointment_agent")



    auth_agent_builder = StateGraph(State, config_schema=Configuration)
    auth_agent_builder.add_node("auth_node", authentication_node)
    auth_agent_builder.add_node("auth_tools", ToolNode(authentication_tools))
    auth_agent_builder.add_edge(START, "auth_node")
    auth_agent_builder.add_conditional_edges(
        "auth_node",
        should_continue,         
        {
            "continue": "auth_tools",
            "end": END,
        },
    )
    auth_agent_builder.add_edge("auth_tools", "auth_node")

    if add_checkpoint:
        auth_agent = auth_agent_builder.compile(name="auth_agent", checkpointer=MemorySaver())
    else:
        auth_agent = auth_agent_builder.compile(name="auth_agent")


    multi_agent_builder = StateGraph(State, config_schema=Configuration)
    multi_agent_builder.add_node("appointment_agent", appointment_agent)
    multi_agent_builder.add_node("auth_agent", auth_agent)

    multi_agent_builder.add_edge(START, "appointment_agent")

    if add_checkpoint:
        return multi_agent_builder.compile(name="multi_agent", checkpointer=MemorySaver())
    else:
        return multi_agent_builder.compile(name="multi_agent")


multi_agent = build_agent(add_checkpoint=True)
langgraph_multi_agent = build_agent(add_checkpoint=False)
