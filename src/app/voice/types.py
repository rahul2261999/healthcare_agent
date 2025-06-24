from enum import Enum
from typing import Optional, Any, Dict, Union, Literal

from pydantic import BaseModel, Field
from pydantic import model_validator


# Enum names suffixed with Enum to avoid shadowing field names


class CallDirectionEnum(str, Enum):
    inbound = "inbound"
    outbound_api = "outbound-api"
    outbound_dial = "outbound-dial"
    outbound_resque = "outbound-resqueue"


# noqa: WPS110 – Twilio naming preserved


class CallStatusEnum(str, Enum):
    queued = "queued"
    ringing = "ringing"
    in_progress = "in-progress"
    completed = "completed"
    busy = "busy"
    failed = "failed"
    no_answer = "no-answer"
    canceled = "canceled"


class TwilioCommonParams(BaseModel):
    """Core request parameters Twilio includes on every voice webhook."""

    AccountSid: str
    ApiVersion: str
    CallSid: str
    CallStatus: Optional[CallStatusEnum] = None
    Direction: Optional[CallDirectionEnum] = None

    From: str
    To: str

    Caller: Optional[str] = None
    Called: Optional[str] = None

    # Geo data (may be blank for some numbers)
    FromCity: Optional[str] = None
    FromState: Optional[str] = None
    FromZip: Optional[str] = None
    FromCountry: Optional[str] = None

    ToCity: Optional[str] = None
    ToState: Optional[str] = None
    ToZip: Optional[str] = None
    ToCountry: Optional[str] = None

    CallerCity: Optional[str] = None
    CallerState: Optional[str] = None
    CallerZip: Optional[str] = None
    CallerCountry: Optional[str] = None

    CalledCity: Optional[str] = None
    CalledState: Optional[str] = None
    CalledZip: Optional[str] = None
    CalledCountry: Optional[str] = None

    ForwardedFrom: Optional[str] = None
    ParentCallSid: Optional[str] = None
    SipCallId: Optional[str] = None

    class Config:
        extra = "allow"  # allow provider-specific or future params


class TtsProviderEnum(str, Enum):
    elevenlabs = "ElevenLabs"  # default in twilio
    google = "Google"
    amazon = "Amazon"


class InterruptibleEnum(str, Enum):
    none = "none"
    dtmf = "dtmf"
    speech = "speech"
    any = "any"


class TextNormalizationEnum(str, Enum):
    on = "on"
    auto = "auto"
    off = "off"


class ConversationRelayAttributes(BaseModel):
    """Twilio ConversationRelay attributes for configuring real-time voice conversations."""

    # Required
    url: str

    # Optional with defaults
    welcome_greeting: Optional[str] = None
    welcome_greeting_interruptible: InterruptibleEnum = InterruptibleEnum.any
    language: str = "en-US"
    tts_language: Optional[str] = None
    tts_provider: Optional[TtsProviderEnum] = None  # default in twilio (elevenlabs)
    voice: Optional[str] = None  # Provider-specific defaults handled in logic
    transcription_language: Optional[str] = None
    transcription_provider: Optional[TtsProviderEnum] = (
        None  # default in twilio (google)
    )
    speech_model: Optional[str] = None  # Provider-specific defaults handled in logic
    interruptible: Optional[InterruptibleEnum] = None  # default in twilio (any)
    dtmf_detection: Optional[bool] = None
    report_input_during_agent_speech: Optional[InterruptibleEnum] = (
        None  # default in twilio (none)
    )
    preemptible: bool = False
    hints: Optional[str] = None  # Comma-separated list
    debug: Optional[str] = None  # Space-separated list
    elevenlabs_text_normalization: Optional[TextNormalizationEnum] = (
        None  # default in twilio (off)
    )
    intelligence_service: Optional[str] = None


# ---------------------------------------------------------------------------
# Twilio ConversationRelay Web-Socket Messages (Inbound & Outbound)
# ---------------------------------------------------------------------------


class ConversationRelayMessageTypeEnum(str, Enum):
    """All message types exchanged over the ConversationRelay Web-Socket."""

    # Messages **received** from Twilio
    setup = "setup"
    prompt = "prompt"
    dtmf = "dtmf"
    interrupt = "interrupt"
    error = "error"

    # Messages **sent** to Twilio
    text = "text"
    play = "play"
    send_digits = "sendDigits"
    language = "language"
    end = "end"


class CRBaseMessage(BaseModel):
    """Common attributes every Web-Socket message includes."""

    type: ConversationRelayMessageTypeEnum

    model_config = {"extra": "allow", "populate_by_name": True}


# -----------------------------
# Inbound messages (Twilio → Us)
# -----------------------------


class CRSetupMessage(CRBaseMessage):
    type: Literal[ConversationRelayMessageTypeEnum.setup] = (
        ConversationRelayMessageTypeEnum.setup
    )  # noqa: E501
    sessionId: str
    callSid: str
    from_: str = Field(..., alias="from")  
    to: str = Field(..., alias="to")
    direction: CallDirectionEnum
    customParameters: Optional[Dict[str, Any]] = None


class CRPromptMessage(CRBaseMessage):
    type: Literal[ConversationRelayMessageTypeEnum.prompt] = (
        ConversationRelayMessageTypeEnum.prompt
    )  # noqa: E501
    voicePrompt: str
    lang: str = "en-US"
    last: bool = False


class CRDtmfMessage(CRBaseMessage):
    type: Literal[ConversationRelayMessageTypeEnum.dtmf] = (
        ConversationRelayMessageTypeEnum.dtmf
    )  # noqa: E501
    digit: str  # single DTMF digit


class CRInterruptMessage(CRBaseMessage):
    type: Literal[ConversationRelayMessageTypeEnum.interrupt] = (
        ConversationRelayMessageTypeEnum.interrupt
    )  # noqa: E501
    utteranceUntilInterrupt: str
    durationUntilInterruptMs: int


class CRErrorMessage(CRBaseMessage):
    type: Literal[ConversationRelayMessageTypeEnum.error] = (
        ConversationRelayMessageTypeEnum.error
    )  # noqa: E501
    description: str


# -----------------------------
# Outbound messages (Us → Twilio)
# -----------------------------


class CRTextMessage(CRBaseMessage):
    type: Literal[ConversationRelayMessageTypeEnum.text] = (
        ConversationRelayMessageTypeEnum.text
    )  # noqa: E501
    token: str
    last: bool = False
    interruptible: Optional[bool] = None
    preemptible: Optional[bool] = None
    lang: Optional[str] = None


class CRPlayMessage(CRBaseMessage):
    type: Literal[ConversationRelayMessageTypeEnum.play] = (
        ConversationRelayMessageTypeEnum.play
    )  # noqa: E501
    source: str  # URL of the media to play
    loop: Optional[int] = 1
    preemptible: Optional[bool] = None
    interruptible: Optional[bool] = None


class CRSendDigitsMessage(CRBaseMessage):
    type: Literal[ConversationRelayMessageTypeEnum.send_digits] = (
        ConversationRelayMessageTypeEnum.send_digits
    )  # noqa: E501
    digits: str


# noinspection PyPep8Naming – keep in sync with Twilio's JSON schema
class CRLanguageMessage(CRBaseMessage):
    type: Literal[ConversationRelayMessageTypeEnum.language] = (
        ConversationRelayMessageTypeEnum.language
    )  # noqa: E501
    ttsLanguage: Optional[str] = None
    transcriptionLanguage: Optional[str] = None

    @model_validator(mode="after")
    def _ensure_language_specified(self):  # type: ignore[return-value]
        """Ensure at least one of the optional language attributes is set."""
        if not (self.ttsLanguage or self.transcriptionLanguage):
            raise ValueError(
                "Either 'ttsLanguage' or 'transcriptionLanguage' must be provided."
            )
        return self


class CREndMessage(CRBaseMessage):
    type: Literal[ConversationRelayMessageTypeEnum.end] = (
        ConversationRelayMessageTypeEnum.end
    )  # noqa: E501
    handoffData: Optional[str] = None


# -----------------------------
# Helper discriminated unions
# -----------------------------

ConversationRelayInboundMessage = Union[
    CRSetupMessage,
    CRPromptMessage,
    CRDtmfMessage,
    CRInterruptMessage,
    CRErrorMessage,
]

ConversationRelayOutboundMessage = Union[
    CRTextMessage,
    CRPlayMessage,
    CRSendDigitsMessage,
    CRLanguageMessage,
    CREndMessage,
]


# ---------------------------------------------------------------------------
# Twilio Webhooks & Callbacks
# ---------------------------------------------------------------------------


class TwilioVoiceWebhook(TwilioCommonParams):
    """Extends common params with any others we care about at runtime."""

    class Config:
        extra = "allow"


class CallStatusCallback(TwilioCommonParams):
    """Parameters Twilio sends to the action/statusCallback when a call ends."""

    CallDuration: Optional[str] = None
    RecordingUrl: Optional[str] = None
    RecordingSid: Optional[str] = None
    RecordingDuration: Optional[str] = None

    class Config:
        extra = "allow"


class SecureTwilioWebhook(TwilioCommonParams):
    """Stricter version of the webhook payload.

    * Disallows unknown fields (`extra='forbid'`).
    * Adds a tenant identifier for multi-tenant routing.
    * Enforces HTTPS on any *Url field we care about.
    """

    TenantId: str = Field(..., alias="tenant_id")

    model_config = {
        **TwilioCommonParams.model_config,
        "populate_by_name": True,
    }
