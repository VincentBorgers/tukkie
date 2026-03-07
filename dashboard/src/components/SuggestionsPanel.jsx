import SectionCard from "./SectionCard";

export default function SuggestionsPanel({ suggestions = [], automations = [] }) {
  return (
    <SectionCard title="Automatiseringssuggesties" kicker="Adaptief leren">
      <div className="space-y-3">
        {suggestions.length === 0 ? (
          <div className="rounded-[24px] bg-white/70 p-4 text-sm text-ink/70">
            Nog geen nieuwe suggesties. Gebruik de chat of toolacties zodat Tukkie patronen kan leren.
          </div>
        ) : null}
        {suggestions.map((suggestion) => (
          <article key={`${suggestion.title}-${suggestion.created_at}`} className="rounded-[24px] bg-white/75 p-4 shadow-sm">
            <div className="flex items-center justify-between gap-4">
              <h3 className="text-base font-semibold text-ink">{suggestion.title}</h3>
              <span className="rounded-full bg-clay/20 px-3 py-1 text-xs font-medium text-clay">
                {(suggestion.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <p className="mt-2 text-sm leading-6 text-ink/75">{suggestion.description}</p>
          </article>
        ))}
      </div>

      <div className="mt-5 rounded-[24px] bg-ink px-5 py-4 text-white">
        <p className="text-xs uppercase tracking-[0.3em] text-white/60">Huidige automatiseringen</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {automations.length === 0 ? (
            <span className="rounded-full border border-white/20 px-3 py-2 text-sm text-white/70">Nog geen regels opgeslagen</span>
          ) : (
            automations.map((automation) => (
              <span key={automation.id} className="rounded-full border border-white/20 px-3 py-2 text-sm text-white/80">
                {automation.name}
              </span>
            ))
          )}
        </div>
      </div>
    </SectionCard>
  );
}
