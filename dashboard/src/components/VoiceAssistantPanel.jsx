import { useEffect, useRef, useState } from "react";

import SectionCard from "./SectionCard";

function encodeWav(chunks, sampleRate) {
  const mergedLength = chunks.reduce((total, chunk) => total + chunk.length, 0);
  const buffer = new ArrayBuffer(44 + mergedLength * 2);
  const view = new DataView(buffer);

  const writeString = (offset, value) => {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset + index, value.charCodeAt(index));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + mergedLength * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, mergedLength * 2, true);

  let offset = 44;
  chunks.forEach((chunk) => {
    for (let index = 0; index < chunk.length; index += 1) {
      const sample = Math.max(-1, Math.min(1, chunk[index]));
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
      offset += 2;
    }
  });

  return new Blob([buffer], { type: "audio/wav" });
}

export default function VoiceAssistantPanel({ voiceStatus, onTranscribeAndChat, busy }) {
  const [recording, setRecording] = useState(false);
  const [voiceError, setVoiceError] = useState("");
  const [meter, setMeter] = useState(0);
  const chunksRef = useRef([]);
  const audioContextRef = useRef(null);
  const streamRef = useRef(null);
  const processorRef = useRef(null);
  const sourceRef = useRef(null);

  useEffect(() => {
    return () => {
      stopCapture();
    };
  }, []);

  const startCapture = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setVoiceError("Je browser ondersteunt geen lokale microfoontoegang.");
      return;
    }

    try {
      chunksRef.current = [];
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        }
      });
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      const context = new AudioContextClass();
      const source = context.createMediaStreamSource(stream);
      const processor = context.createScriptProcessor(4096, 1, 1);

      processor.onaudioprocess = (event) => {
        const channelData = event.inputBuffer.getChannelData(0);
        chunksRef.current.push(new Float32Array(channelData));
        const peak = channelData.reduce((max, value) => Math.max(max, Math.abs(value)), 0);
        setMeter(peak);
      };

      source.connect(processor);
      processor.connect(context.destination);

      audioContextRef.current = context;
      streamRef.current = stream;
      processorRef.current = processor;
      sourceRef.current = source;
      setVoiceError("");
      setRecording(true);
    } catch (error) {
      setVoiceError("Microfoon kon niet worden geopend.");
    }
  };

  const stopCapture = async () => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current.onaudioprocess = null;
      processorRef.current = null;
    }
    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current) {
      await audioContextRef.current.close();
      audioContextRef.current = null;
    }
    setMeter(0);
    setRecording(false);
  };

  const finishCapture = async () => {
    const sampleRate = audioContextRef.current?.sampleRate || 16000;
    const blob = encodeWav(chunksRef.current, sampleRate);
    await stopCapture();
    await onTranscribeAndChat(blob);
  };

  const sttReady = voiceStatus?.stt?.available;
  const ttsReady = voiceStatus?.tts?.available;

  return (
    <SectionCard
      title="Spraakassistent"
      kicker="Lokale spraak"
      actions={
        <div className="flex items-center gap-2">
          <span className={`status-pill ${sttReady ? "status-pill--ok" : "status-pill--warn"}`}>
            STT {sttReady ? "gereed" : "mist model"}
          </span>
          <span className={`status-pill ${ttsReady ? "status-pill--ok" : "status-pill--warn"}`}>
            TTS {ttsReady ? "gereed" : "nog niet"}
          </span>
        </div>
      }
    >
      <div className="space-y-4">
        <div className="voice-orb-shell">
          <button
            type="button"
            className={`voice-orb ${recording ? "voice-orb--recording" : ""}`}
            disabled={busy}
            onClick={recording ? finishCapture : startCapture}
          >
            {recording ? "Stop" : "Spreek"}
          </button>
          <div className="voice-meter">
            <div className="voice-meter__fill" style={{ width: `${Math.max(8, meter * 100)}%` }} />
          </div>
        </div>

        <p className="text-sm leading-6 text-ink/75">
          Gebruik de microfoonknop om lokaal een WAV-opname te maken. De backend verwerkt die met Vosk zodra een
          Nederlands model aanwezig is en spreekt terug via Piper als TTS is geconfigureerd.
        </p>

        {voiceError ? <p className="rounded-2xl bg-clay/10 px-4 py-3 text-sm text-ink">{voiceError}</p> : null}

        <div className="space-y-2 rounded-[24px] bg-ink/5 p-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-ink/60">Speech-to-text</span>
            <span className="font-medium text-ink">{voiceStatus?.stt?.provider || "vosk"}</span>
          </div>
          <p className="text-sm text-ink/70">{voiceStatus?.stt?.reason}</p>
          <div className="flex items-center justify-between text-sm">
            <span className="text-ink/60">Text-to-speech</span>
            <span className="font-medium text-ink">{voiceStatus?.tts?.provider || "piper"}</span>
          </div>
          <p className="text-sm text-ink/70">{voiceStatus?.tts?.reason}</p>
        </div>
      </div>
    </SectionCard>
  );
}
