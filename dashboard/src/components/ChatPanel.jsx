import SectionCard from "./SectionCard";

const starterPrompts = [
  "Zet de woonkamerverlichting aan",
  "Wat is de status van de opritcamera?",
  "Analyseer mijn netwerk",
  "Welke routines zie je?"
];

export default function ChatPanel({
  messages,
  input,
  onInputChange,
  onSend,
  loading,
  pendingConfirmation,
  onConfirm
}) {
  return (
    <SectionCard
      title="AI Chat"
      kicker="Lokale Assistent"
      actions={
        pendingConfirmation ? (
          <button className="soft-button" onClick={onConfirm} type="button">
            Bevestig kritieke actie
          </button>
        ) : null
      }
      className="min-h-[620px]"
    >
      <div className="flex h-full flex-col">
        <div className="grid gap-2 md:grid-cols-2">
          {starterPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="rounded-2xl border border-white/60 bg-white/50 px-4 py-3 text-left text-sm text-ink/80 transition hover:border-clay hover:bg-white"
              onClick={() => onSend(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>

        <div className="mt-5 flex-1 space-y-3 overflow-y-auto rounded-[26px] bg-ink/5 p-4">
          {messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`max-w-[85%] rounded-[24px] px-4 py-3 text-sm leading-6 ${
                message.role === "user"
                  ? "ml-auto bg-ink text-white"
                  : "bg-white/80 text-ink shadow-sm"
              }`}
            >
              {message.content}
            </div>
          ))}
          {loading ? (
            <div className="max-w-[60%] rounded-[24px] bg-white/80 px-4 py-3 text-sm text-ink shadow-sm">
              Tukkie analyseert lokaal...
            </div>
          ) : null}
        </div>

        <form
          className="mt-5 flex flex-col gap-3 md:flex-row"
          onSubmit={(event) => {
            event.preventDefault();
            onSend();
          }}
        >
          <textarea
            value={input}
            onChange={(event) => onInputChange(event.target.value)}
            className="min-h-[96px] flex-1 rounded-[24px] border border-white/70 bg-white/80 px-5 py-4 text-sm text-ink outline-none transition focus:border-clay"
            placeholder="Vraag iets in het Nederlands, bijvoorbeeld: 'Ik schakel meestal rond 20:30 de avondscène in.'"
          />
          <button className="primary-button md:min-w-[180px]" type="submit" disabled={loading}>
            {loading ? "Bezig..." : "Versturen"}
          </button>
        </form>
      </div>
    </SectionCard>
  );
}
