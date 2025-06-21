from mock.agent import AgentConfig
from agent.state import MainState
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from core.prebuilt.idv_agent.tools.tools import (
    send_otp,
    verify_otp,
    set_phone_number,
    validate_payload,
    confirm_authorization,
)
from utils.utils import create_handoff_tool
from core.agent_builder.agent_builder import AgentBuilder


class IdvAgent:
    def __init__(self, protected_agents: list[AgentConfig]):
        self.protected_agents = protected_agents

    def _build_prompt(self):

        def agent_prompt(state: MainState) -> str:
            print(f"IDVBuilder: building idv agent prompt")

            system_prompt = f"""
        You are an intelligent user authentication agent. Your role is to authenticate users using the tools at your disposal.      
        ---

        **Context Variables**:
        - `is_authorized` is {state.get('is_authorized')}
        - `otp_sent` is {state.get('otp_sent')}

        ---

        **Flow Logic**:
        first check the user's authorization status using `confirm_authorization` tool.

        ### 1. Authorization Check
        - If `is_authorized` is True:
          - Immediately return control using the correct `transfer` tool at your disposal. determine which agent originally triggered the authentication request.
          - Once the handoff is done, do not send any further messages.

        ### 2. Authentication Flow (if `is_authorized` is False)
          #### a. Payload Validation
          - Always begin by calling `validate_payload` — regardless of input completeness.
          - Wait for the tool response:
            - If validation fails due to missing/invalid fields:
              - Prompt the user with clear instructions (without exposing system internals) for what is needed.
              - Upon user response, call the appropriate tool to update state and then retry `validate_payload`.

          #### b. OTP Flow
          - If validation is successful:
            - If `otp_sent` is False, call `send_otp`.
            - If `otp_sent` is True:
              - If the user provides a valid 6-digit OTP, call `verify_otp`.
              - If OTP is correct:
                - Return control via the correct `handoff` tool as described in Step 1.
              - If OTP fails:
                - Allow up to 2 retries.
                - After 2 failed attempts, ask the user if they want to resend the OTP.
                - If they agree, call `send_otp` again.
        ---

        **Tool Usage Protocol**:
        - Use **only one tool at a time, parallel tool call is not allowed**.
        - Never expose state keys, tool names, or backend logic in any message.

        ---

        **Fallback Option**:
        - You may use `confirm_authorization` at any point to verify the user's authentication status.
        
        Important Rules:
         - Flow execution and decision making should be based on the tools output and past conversation history.
         - Ignore any tool messages that state "successfully transferred", "handoff complete", or similar. Proceed with the next step.
        """

            return [SystemMessage(content=system_prompt)] + state["messages"] # type: ignore

        return agent_prompt

    def _build_handoff_tools(self):
        print(f"IDVBuilder: building handoff tools")

        handoff_tools = []

        for agent in self.protected_agents:
            print(
                f"IDVBuilder: building handoff tool for agent: {AgentBuilder.sanitize_string(agent.get('display_name'))}"
            )

            transfer_to_agent = create_handoff_tool(
                agent_name=AgentBuilder.sanitize_string(agent.get("display_name")),
                description=f"Transfer user to the {AgentBuilder.sanitize_string(agent.get('display_name'))} assistant for authentication.",
                include_state_keys=["is_authorized", "otp_sent", "phone_number"],
            )

            handoff_tools.append(transfer_to_agent)

        print(f"IDVBuilder: handoff tools built successfully")

        return handoff_tools

    def get_idv_handoff_tools(self):
        print(f"IDVBuilder: getting idv handoff tools")

        transfer_to_idv_agent = create_handoff_tool(
            agent_name="idv_agent",
            description="Transfer user to the idv_agent for authentication or to check user authorization status.",
        )

        return transfer_to_idv_agent

    def build(self):
        print(f"IDVBuilder: building idv agent")

        handoff_tools = self._build_handoff_tools()

        idv_agent = create_react_agent(
            model=ChatOpenAI(model="gpt-4o-mini"),
            tools=[
                set_phone_number,
                send_otp,
                verify_otp,
                validate_payload,
                confirm_authorization,
                *handoff_tools,
            ],
            state_schema=MainState,
            name="idv_agent",
            prompt=self._build_prompt(),
        )

        transfer_to_idv_agent = self.get_idv_handoff_tools()

        print(f"IDVBuilder: idv agent built successfully")

        return idv_agent, transfer_to_idv_agent
