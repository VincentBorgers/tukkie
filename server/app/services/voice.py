from __future__ import annotations

import io
import json
import subprocess
import wave
from pathlib import Path
from uuid import uuid4

try:
    import vosk
except ImportError:  # pragma: no cover
    vosk = None

if vosk is not None:  # pragma: no cover
    vosk.SetLogLevel(-1)


class VoiceService:
    def __init__(self, settings):
        self.settings = settings
        self._vosk_model = None

    def status(self) -> dict:
        vosk_model_path = Path(self.settings.vosk_model_path)
        piper_binary_path = Path(self.settings.piper_binary_path) if self.settings.piper_binary_path else None
        piper_model_path = Path(self.settings.piper_voice_model_path) if self.settings.piper_voice_model_path else None

        stt_available = bool(self.settings.voice_input_enabled and vosk is not None and vosk_model_path.exists())
        tts_available = bool(
            self.settings.enable_voice_blueprint
            and piper_binary_path
            and piper_model_path
            and piper_binary_path.exists()
            and piper_model_path.exists()
        )

        return {
            "enabled": self.settings.enable_voice_blueprint,
            "auto_speak": self.settings.voice_auto_speak,
            "stt": {
                "provider": "vosk",
                "available": stt_available,
                "model_path": str(vosk_model_path),
                "reason": self._stt_reason(vosk_model_path),
            },
            "tts": {
                "provider": "piper",
                "available": tts_available,
                "binary_path": str(piper_binary_path) if piper_binary_path else "",
                "model_path": str(piper_model_path) if piper_model_path else "",
                "reason": self._tts_reason(piper_binary_path, piper_model_path),
            },
        }

    def transcribe_wav(self, audio_bytes: bytes) -> dict:
        status = self.status()
        if not status["stt"]["available"]:
            raise RuntimeError(status["stt"]["reason"])

        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()
            frames = wav_file.readframes(frame_count)

        if channels != 1 or sample_width != 2:
            raise RuntimeError("Gebruik mono 16-bit PCM WAV audio voor lokale transcriptie.")

        recognizer = vosk.KaldiRecognizer(self._load_vosk_model(), sample_rate)
        recognizer.SetWords(True)

        chunk_size = 4000
        for offset in range(0, len(frames), chunk_size):
            recognizer.AcceptWaveform(frames[offset : offset + chunk_size])

        result = json.loads(recognizer.FinalResult() or "{}")
        transcript = (result.get("text") or "").strip()

        return {
            "transcript": transcript,
            "sample_rate": sample_rate,
            "channels": channels,
            "seconds": round(frame_count / sample_rate, 2) if sample_rate else 0,
            "words": result.get("result", []),
        }

    def synthesize(self, text: str) -> bytes:
        status = self.status()
        if not status["tts"]["available"]:
            raise RuntimeError(status["tts"]["reason"])

        binary_path = Path(self.settings.piper_binary_path)
        model_path = Path(self.settings.piper_voice_model_path)
        output_path = self.settings.voice_cache_path / f"{uuid4().hex}.wav"

        command = [
            str(binary_path),
            "--model",
            str(model_path),
            "--output_file",
            str(output_path),
        ]
        if self.settings.piper_voice_config_path and Path(self.settings.piper_voice_config_path).exists():
            command.extend(["--config", str(self.settings.piper_voice_config_path)])

        input_text = text.strip()
        if not input_text.endswith((".", "!", "?")):
            input_text += "."

        result = subprocess.run(
            command,
            input=input_text.encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=45,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="ignore").strip()
            raise RuntimeError(stderr or "Piper kon geen audio genereren.")

        audio = output_path.read_bytes()
        output_path.unlink(missing_ok=True)
        return audio

    def _load_vosk_model(self):
        if self._vosk_model is None:
            self._vosk_model = vosk.Model(str(self.settings.vosk_model_path))
        return self._vosk_model

    @staticmethod
    def _stt_reason(model_path: Path) -> str:
        if not model_path.exists():
            return "Vosk-model niet gevonden. Plaats een Nederlands model in het ingestelde pad."
        if vosk is None:
            return "Python package 'vosk' is niet geïnstalleerd."
        return "Lokale transcriptie is gereed."

    @staticmethod
    def _tts_reason(binary_path: Path | None, model_path: Path | None) -> str:
        if binary_path is None:
            return "Piper binary pad is nog niet ingesteld."
        if not binary_path.exists():
            return "Piper binary niet gevonden."
        if model_path is None or not model_path.exists():
            return "Piper stemmodel niet gevonden."
        return "Lokale spraaksynthese is gereed."
