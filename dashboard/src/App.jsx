import { useEffect, useState } from "react";

import ActivityPanel from "./components/ActivityPanel";
import CameraFeeds from "./components/CameraFeeds";
import ChatPanel from "./components/ChatPanel";
import DeviceControls from "./components/DeviceControls";
import RoomsOverview from "./components/RoomsOverview";
import SectionCard from "./components/SectionCard";
import SetupPanel from "./components/SetupPanel";
import StatusStrip from "./components/StatusStrip";
import SuggestionsPanel from "./components/SuggestionsPanel";
import VoiceAssistantPanel from "./components/VoiceAssistantPanel";
import { executeTool, getOverview, getVoiceBlueprint, sendChat, speakText, transcribeVoice } from "./lib/api";

const initialMessages = [
  {
    role: "assistant",
    content:
      "Ik ben Tukkie. Ik draai lokaal, spreek Nederlands en gebruik alleen gecontroleerde tools voor acties in huis."
  }
];

function MetricRow({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-ink/10 py-3 text-sm last:border-b-0">
      <span className="text-ink/60">{label}</span>
      <span className="max-w-[62%] text-right font-medium text-ink">{value}</span>
    </div>
  );
}

function SummaryChip({ label, value }) {
  return (
    <div className="rounded-[22px] border border-white/40 bg-white/70 px-4 py-4 shadow-sm backdrop-blur">
      <p className="text-xs uppercase tracking-[0.28em] text-ink/40">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

export default function App() {
  const [overview, setOverview] = useState(null);
  const [voiceBlueprint, setVoiceBlueprint] = useState(null);
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [voiceBusy, setVoiceBusy] = useState(false);
  const [busyAction, setBusyAction] = useState("");
  const [pendingConfirmation, setPendingConfirmation] = useState(null);
  const [loadError, setLoadError] = useState("");

  const loadDashboard = async () => {
    try {
      const [nextOverview, nextVoiceBlueprint] = await Promise.all([getOverview(), getVoiceBlueprint()]);
      setOverview(nextOverview);
      setVoiceBlueprint(nextVoiceBlueprint);
      setLoadError("");
    } catch (error) {
      setLoadError("Dashboard kon de lokale API niet bereiken. Start eerst de backend.");
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const pushAssistantMessage = (content) => {
    setMessages((current) => [...current, { role: "assistant", content }]);
  };

  const playReply = async (text) => {
    const blob = await speakText(text);
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.addEventListener("ended", () => URL.revokeObjectURL(url), { once: true });
    await audio.play();
  };

  const handleSend = async (draft = input, confirmationToken = null, options = {}) => {
    const nextMessage = draft.trim();
    if (!nextMessage) {
      return null;
    }

    setMessages((current) => [
      ...current,
      { role: "user", content: confirmationToken ? `Bevestig: ${nextMessage}` : nextMessage }
    ]);

    setInput("");
    setLoading(true);

    try {
      const response = await sendChat(nextMessage, "dashboard", confirmationToken);
      pushAssistantMessage(response.reply);

      if (response.requires_confirmation) {
        setPendingConfirmation({
          mode: "chat",
          message: nextMessage,
          token: response.confirmation_token
        });
      } else {
        setPendingConfirmation(null);
      }

      if (options.spokenReply && voiceBlueprint?.status?.tts?.available) {
        try {
          await playReply(response.reply);
        } catch (error) {
          pushAssistantMessage("De tekstreactie is klaar, maar lokale spraaksynthese kon niet worden afgespeeld.");
        }
      }

      await loadDashboard();
      return response;
    } catch (error) {
      pushAssistantMessage("Er ging iets mis tijdens de lokale verwerking van je bericht.");
      return null;
    } finally {
      setLoading(false);
    }
  };

  const handleToolAction = async (toolName, payload, actionKey, confirmationToken = null) => {
    setBusyAction(actionKey);

    try {
      const result = await executeTool(toolName, payload, confirmationToken);
      pushAssistantMessage(result.message);

      if (result.requires_confirmation) {
        setPendingConfirmation({
          mode: "tool",
          toolName,
          payload,
          token: result.confirmation_token,
          actionKey
        });
      } else {
        setPendingConfirmation(null);
      }

      await loadDashboard();
    } catch (error) {
      pushAssistantMessage("De gevraagde toolactie kon niet veilig worden uitgevoerd.");
    } finally {
      setBusyAction("");
    }
  };

  const confirmPendingAction = async () => {
    if (!pendingConfirmation) {
      return;
    }

    const pending = pendingConfirmation;
    setPendingConfirmation(null);

    if (pending.mode === "chat") {
      await handleSend(pending.message, pending.token);
      return;
    }

    await handleToolAction(pending.toolName, pending.payload, pending.actionKey, pending.token);
  };

  const handleVoiceChat = async (audioBlob) => {
    setVoiceBusy(true);

    try {
      const transcription = await transcribeVoice(audioBlob);
      if (!transcription.transcript) {
        pushAssistantMessage("Ik hoorde audio, maar kon er geen bruikbare Nederlandse transcriptie uit halen.");
        return;
      }

      await handleSend(transcription.transcript, null, { spokenReply: true });
    } catch (error) {
      pushAssistantMessage("Spraakverwerking is nog niet beschikbaar. Controleer het Vosk-modelpad in het project.");
    } finally {
      setVoiceBusy(false);
    }
  };

  const voiceStatus = voiceBlueprint?.status || overview?.voice;
  const setup = overview?.setup;

  return (
    <div className="min-h-screen px-4 py-5 md:px-8 xl:px-10">
      <div className="mx-auto max-w-[1820px]">
        <section className="hero-shell">
          <div className="hero-grid">
            <div>
              <p className="text-xs uppercase tracking-[0.45em] text-ink/40">Open-Source Local Home Intelligence</p>
              <h1 className="mt-4 text-4xl font-semibold leading-tight text-ink md:text-6xl">
                Tukkie
              </h1>
              <p className="mt-5 max-w-3xl text-base leading-7 text-ink/70">
                Een lokale Nederlandse home intelligence cockpit voor chat, geheugen, automatiseringen, device-status,
                netwerkobservaties en voice-uitbreiding, ontworpen voor configureerbare open-source deployments.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <span className="status-pill status-pill--ok">SQLite geheugen</span>
                <span className={`status-pill ${overview?.assistant?.ollama_available ? "status-pill--ok" : "status-pill--warn"}`}>
                  Ollama {overview?.assistant?.ollama_available ? "online" : "offline"}
                </span>
                <span className={`status-pill ${voiceStatus?.stt?.available ? "status-pill--ok" : "status-pill--warn"}`}>
                  Voice input {voiceStatus?.stt?.available ? "gereed" : "setup nodig"}
                </span>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-2">
              <SummaryChip label="Ruimtes" value={overview?.home_status?.rooms_online || 0} />
              <SummaryChip label="Devices online" value={overview?.home_status?.devices_online || 0} />
              <SummaryChip label="Integraties actief" value={overview?.home_status?.integrations_connected || 0} />
              <SummaryChip label="Automations" value={overview?.home_status?.automation_count || 0} />
            </div>
          </div>
        </section>

        {loadError ? (
          <div className="mt-6 rounded-[24px] border border-clay/30 bg-clay/10 px-5 py-4 text-sm text-ink">
            {loadError}
          </div>
        ) : null}

        <div className="mt-6">
          <StatusStrip assistant={overview?.assistant} homeStatus={overview?.home_status} />
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.32fr_0.88fr]">
          <div className="space-y-6">
            <ChatPanel
              messages={messages}
              input={input}
              onInputChange={setInput}
              onSend={handleSend}
              loading={loading}
              pendingConfirmation={pendingConfirmation}
              onConfirm={confirmPendingAction}
            />
            <div className="grid gap-6 2xl:grid-cols-2">
              <SuggestionsPanel suggestions={overview?.suggestions || []} automations={overview?.automations || []} />
              <ActivityPanel activity={overview?.activity || []} />
            </div>
            <div className="grid gap-6 2xl:grid-cols-2">
              <RoomsOverview rooms={overview?.rooms || []} scenes={overview?.scenes || []} />
              <DeviceControls
                devices={overview?.devices || []}
                onRunTool={handleToolAction}
                busyAction={busyAction}
              />
            </div>
            <CameraFeeds cameras={overview?.cameras || []} />
          </div>

          <div className="space-y-6">
            <VoiceAssistantPanel
              voiceStatus={voiceStatus}
              onTranscribeAndChat={handleVoiceChat}
              busy={voiceBusy || loading}
            />
            <SetupPanel setup={setup} />

            <SectionCard title="Network Status" kicker="Analyse zonder destructieve acties">
              <MetricRow label="Zichtbare apparaten" value={overview?.network?.devices?.length || 0} />
              <MetricRow label="Afwijkingsscore" value={overview?.network?.anomaly_score?.toFixed?.(2) || "0.00"} />
              <MetricRow label="Samenvatting" value={overview?.network?.summary || "Nog geen snapshot"} />
            </SectionCard>

            <SectionCard title="Energy Usage" kicker="Lokaal berekend">
              <MetricRow label="Schatting huidig verbruik" value={`${overview?.energy?.estimated_watts || 0} W`} />
              <MetricRow label="Actieve devices" value={overview?.energy?.active_devices || 0} />
              <MetricRow label="Analysevenster" value={overview?.energy?.window || "24h"} />
            </SectionCard>

            <SectionCard title="Voice Runtime" kicker="Open-source pipeline">
              <MetricRow
                label="Wake word"
                value={voiceBlueprint?.wake_word || overview?.assistant?.wake_word || "tukkie"}
              />
              <MetricRow label="STT provider" value={voiceStatus?.stt?.provider || "vosk"} />
              <MetricRow label="TTS provider" value={voiceStatus?.tts?.provider || "piper"} />
              <MetricRow label="Auto speak" value={voiceStatus?.auto_speak ? "aan" : "uit"} />
            </SectionCard>
          </div>
        </div>
      </div>
    </div>
  );
}
