from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response

from server.app.bootstrap import ROOT_DIR

from vha_tools.base import ToolContext

from .schemas import ChatRequest, ChatResponse, SpeakRequest, ToolExecutionRequest, VoiceTranscriptionResponse


router = APIRouter()


def _runtime(request: Request):
    return request.app.state.runtime


@router.get("/health")
async def health(request: Request) -> dict:
    return {"status": "ok", "service": _runtime(request).settings.app_name}


@router.get("/api/overview")
async def overview(request: Request) -> dict:
    return _runtime(request).dashboard_overview()


@router.get("/api/rooms")
async def rooms(request: Request) -> list[dict]:
    return _runtime(request).dashboard_overview()["rooms"]


@router.get("/api/devices")
async def devices(request: Request) -> list[dict]:
    return _runtime(request).dashboard_overview()["devices"]


@router.get("/api/suggestions")
async def suggestions(request: Request) -> list[dict]:
    return _runtime(request).dashboard_overview()["suggestions"]


@router.get("/api/activity")
async def activity(request: Request) -> list[dict]:
    return _runtime(request).dashboard_overview()["activity"]


@router.get("/api/tools")
async def tools(request: Request) -> list[dict]:
    return _runtime(request).tool_registry.list_tools()


@router.get("/api/integrations/health")
async def integrations_health(request: Request) -> list[dict]:
    return _runtime(request).integrations.health()


@router.get("/api/setup/status")
async def setup_status(request: Request) -> dict:
    return _runtime(request).setup_status()


@router.get("/api/voice/blueprint")
async def voice_blueprint(request: Request) -> dict:
    runtime = _runtime(request)
    status = runtime.voice.status()
    wake_word = runtime.config_summary.get("voice", {}).get("wake_word", runtime.settings.default_wake_word)
    return {
        "enabled": runtime.settings.enable_voice_blueprint,
        "wake_word": wake_word,
        "stt": status["stt"]["provider"],
        "tts": status["tts"]["provider"],
        "transport_targets": ["phone", "smart-display", "desktop"],
        "status": status,
    }


@router.get("/api/voice/status")
async def voice_status(request: Request) -> dict:
    return _runtime(request).voice.status()


@router.get("/api/cameras/{camera_id}/snapshot")
async def camera_snapshot(camera_id: str, request: Request):
    runtime = _runtime(request)
    camera = runtime.memory.get_device(camera_id)
    if camera is None or camera.type != "camera":
        raise HTTPException(status_code=404, detail="Camera niet gevonden.")

    try:
        snapshot = runtime.integrations.camera_snapshot(camera.model_dump())
    except Exception:
        snapshot = None
    if snapshot is not None:
        content, content_type = snapshot
        return Response(content=content, media_type=content_type)

    placeholder = ROOT_DIR / "dashboard" / "public" / "camera-placeholder.svg"
    return FileResponse(placeholder, media_type="image/svg+xml")


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: Request, payload: ChatRequest) -> ChatResponse:
    runtime = _runtime(request)
    response = await runtime.assistant.handle_message(
        session_id=payload.session_id,
        message=payload.message,
        confirmation_token=payload.confirmation_token,
    )
    return ChatResponse.model_validate(response.model_dump())


@router.post("/api/voice/transcribe", response_model=VoiceTranscriptionResponse)
async def voice_transcribe(request: Request) -> VoiceTranscriptionResponse:
    runtime = _runtime(request)
    audio_bytes = await request.body()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Geen audio ontvangen.")
    try:
        transcript = runtime.voice.transcribe_wav(audio_bytes)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return VoiceTranscriptionResponse.model_validate(transcript)


@router.post("/api/voice/speak")
async def voice_speak(request: Request, payload: SpeakRequest):
    runtime = _runtime(request)
    try:
        audio = runtime.voice.synthesize(payload.text)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(content=audio, media_type="audio/wav")


@router.post("/api/tools/{tool_name}")
async def execute_tool(request: Request, tool_name: str, payload: ToolExecutionRequest) -> dict:
    runtime = _runtime(request)
    result = runtime.tool_registry.execute(
        tool_name,
        payload.payload,
        ToolContext(
            session_id="dashboard",
            memory=runtime.memory,
            integrations=runtime.integrations,
            settings=runtime.settings,
            permission_guard=runtime.permission_guard,
            confirmation_token=payload.confirmation_token,
        ),
    )
    if not result.ok and not result.requires_confirmation:
        raise HTTPException(status_code=400, detail=result.message)
    return result.model_dump()
