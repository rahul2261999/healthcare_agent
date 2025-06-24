from fastapi import (
    APIRouter,
    Request,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    HTTPException,
)
from fastapi.responses import Response, JSONResponse
from typing import Any, Dict, cast

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, HumanMessage, AIMessageChunk
from twilio.twiml.voice_response import Connect, ConversationRelay
from pprint import pformat

from src.agents.agent import appointment_agent
from src.agents.state import AgentBranding, State
from src.lib.logger import logger
from src.mock.customer import customer_store
from src.mock.customer_sessions import customer_session_store, CustomerSession

from .types import (
    CRBaseMessage,
    InterruptibleEnum,
    TwilioVoiceWebhook,
    CallStatusCallback,
    ConversationRelayAttributes,
    ConversationRelayMessageTypeEnum,
    CRPromptMessage,
    CRTextMessage,
    CRErrorMessage,
    CREndMessage,
    CRSetupMessage,
)

from src.app.config import Settings, get_settings

router = APIRouter()


@router.post("", response_class=Response, name="voice-webhook")
async def inbound_call(
    request: Request, settings: Settings = Depends(get_settings)
) -> Response:
    """Handle inbound voice call webhooks from Twilio.

    Twilio hits this endpoint when an inbound phone call is received. We respond with
    TwiML that instructs Twilio to connect the call to Conversation Relay and stream
    the audio to our websocket endpoint for real-time processing.
    """

    form: Dict[str, Any] = await request.form()  # type: ignore[arg-type]
    payload = TwilioVoiceWebhook(**form)  # type: ignore[arg-type]
    logger.debug("Incoming call", extra=payload.model_dump())

    # Build TwiML using Twilio's helper library instead of manual string concat.
    from twilio.twiml.voice_response import (
        VoiceResponse,
    )  # local import avoids cost on cold start

    init_customer_session = customer_session_store.create_session(payload.From, "voice")

    logger.info(f"session created successfully for {payload.From}")

    websocket_url = (
        settings.websocket_url + f"?session_id={init_customer_session.session_id}"
    )
    # callback_url = f"https://{settings.public_host}/voice/callback"

    vr = VoiceResponse()
    connect = Connect()

    conversation_relay_attributes = ConversationRelayAttributes(
        url=websocket_url,
        welcome_greeting="Hello, I am your Ai assistant. I can help you with your appointment and order related queries.",
        welcome_greeting_interruptible=InterruptibleEnum.speech,
        # voice="dMyQqiVXTU80dDl2eNK8",
        voice="dMyQqiVXTU80dDl2eNK8-flash_v2_5-0.8_0.6_0.8",
    )

    conversation_relay_kwargs = conversation_relay_attributes.model_dump(
        mode="json",
        exclude_none=True,
    )

    logger.debug(f"ConversationRelay attributes: {conversation_relay_kwargs}")

    conversation_relay = ConversationRelay(**conversation_relay_kwargs)
    connect.append(conversation_relay)

    vr.append(connect)

    logger.debug(f"Responding with TwiML: {str(vr)}")
    return Response(content=str(vr), media_type="application/xml")


@router.post("/callback", response_class=JSONResponse, name="voice-status-callback")
async def call_status_callback(request: Request) -> JSONResponse:
    """Receive status / action callback once the ConversationRelay session ends."""

    form: Dict[str, Any] = await request.form()  # type: ignore[arg-type]
    data = CallStatusCallback(**form)  # type: ignore[arg-type]
    logger.info("Call completed", extra=data.model_dump())

    # Respond with 204 No Content equivalent -> FastAPI JSONResponse with empty body
    return JSONResponse(status_code=204, content={})


@router.websocket("/ws", name="voice-websocket")
async def conversation_relay_ws(
    websocket: WebSocket,
    session_id: str | None = None,
):  # noqa: WPS217 – single exit acceptable here
    """WebSocket endpoint that Twilio Conversation Relay connects to.

    The implementation below echoes back a simple acknowledgement for every caller
    utterance. Replace the `generate_response` call with real AI/ML logic integrating
    ElevenLabs or any other provider.
    """

    if session_id is None:
        logger.error("Session ID is required")
        raise HTTPException(status_code=400, detail="Session ID is required")

    session = customer_session_store.get_session(session_id)

    if not session:
        logger.error(f"No session found for {session_id}")
        raise HTTPException(status_code=400, detail="Session ID is invalid")

    await websocket.accept()
    logger.info(f"ConversationRelay session established: {websocket.client}")

    try:
        while True:
            raw_msg = await websocket.receive_json()
            logger.debug(f"Received raw message: {raw_msg}")

            inbound = CRBaseMessage(**raw_msg)

            if inbound.type == ConversationRelayMessageTypeEnum.setup:
                inbound_msg = CRSetupMessage(**raw_msg)

                logger.debug(f"Setup received: {inbound_msg.sessionId}")

            elif inbound.type == ConversationRelayMessageTypeEnum.prompt:
                prompt_msg = CRPromptMessage(**raw_msg)
                logger.debug(f"Prompt received: {prompt_msg.voicePrompt}")

                response_message = await generate_response(
                    prompt_msg.voicePrompt, session
                )

                outbound_msg = CRTextMessage(
                    token=response_message,
                    last=True,
                    interruptible=True,
                    preemptible=False,
                )

                logger.debug(
                    f"Sending response: {outbound_msg.model_dump(mode='json', exclude_none=True)}"
                )

                await websocket.send_json(
                    outbound_msg.model_dump(mode="json", exclude_none=True)
                )
                continue

            elif inbound.type == ConversationRelayMessageTypeEnum.error:
                error_msg = CRErrorMessage(**raw_msg)
                logger.error(
                    f"Error from Twilio ConversationRelay: {error_msg.description}"
                )

                raise Exception(
                    f"Error from Twilio ConversationRelay: {error_msg.description}"
                )

            elif inbound.type == ConversationRelayMessageTypeEnum.end:
                end_msg = CREndMessage(**raw_msg)
                logger.info(f"ConversationRelay session ended: {end_msg.handoffData}")

                await websocket.close()
                break

    except WebSocketDisconnect:
        logger.info("ConversationRelay client disconnected")
    except Exception as exc:  # pragma: no cover
        logger.exception("Error in ConversationRelay session: %s", exc)
    finally:
        try:
            await websocket.close()
            customer_session_store.delete_session(session_id)
            logger.debug("ConversationRelay websocket closed")
        except Exception as exc:
            logger.info(f"already closed ConversationRelay websocket: {exc}")


async def generate_response(
    text: str, session: CustomerSession
) -> str:  # noqa: D401 – simple helper
    """Generate a placeholder response.

    This function is intentionally simple. In production you would replace this logic
    with calls to ElevenLabs (STT/TTS) and your favourite LLM to craft a response.
    """

    try:

        customer = customer_store.find_customer_by_phone_number(session.phone_number)

        if not customer:
            raise HTTPException(status_code=400, detail="Customer not found")

        config: RunnableConfig = {
            "configurable": {
                "thread_id": session.session_id,
                "recursion_limit": 10,
            }
        }

        initial_state = State(
            messages=[HumanMessage(content=text)],
            conversation_channel="voice",
            welcome_message="Hello, I am your Ai assistant. I can help you with your appointment related queries.",
            otp_sent=False,
            customer=customer,
            agent_branding=AgentBranding(
                name="Amelia",
                persona="Helpful and courteous",
                tone="Helpful and Casual",
            ),
        )

        response = ""

        async for token, metadata in appointment_agent.astream(
            initial_state.model_dump(), config=config, stream_mode="messages"
        ):
            # Pretty-print the streamed LLM token and its accompanying metadata for easier debugging

            if isinstance(token, AIMessageChunk) and len(token.tool_calls) == 0 and isinstance(token.content, list) and len(token.content) > 0:

                if isinstance(token.content[0], dict) and token.content[0]["type"] == "text":
                    logger.trace(f"Token:\n {pformat(token, indent=2)}")
                    logger.trace(f"Metadata:\n {pformat(metadata)}")

                    response += token.content[0]["text"]

        return response
    except Exception as e:
        logger.error(f"Error generating response: {e}")

        raise e
