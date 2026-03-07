import SectionCard from "./SectionCard";

export default function ActivityPanel({ activity = [] }) {
  return (
    <SectionCard title="Live activiteit" kicker="Leren en analyseren">
      <div className="space-y-3">
        {activity.length === 0 ? (
          <div className="rounded-[24px] bg-white/70 p-4 text-sm text-ink/70">
            Nog geen activiteit vastgelegd. Gebruik de chat, voice of toolacties om gedragsdata op te bouwen.
          </div>
        ) : null}
        {activity.map((item) => (
          <article key={`${item.id}-${item.timestamp}`} className="rounded-[24px] bg-white/80 p-4 shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-ink">{item.action}</p>
                <p className="mt-1 text-sm text-ink/70">
                  {item.device_name || item.room || "Systeem"} · {new Date(item.timestamp).toLocaleString("nl-NL")}
                </p>
              </div>
              <span className="rounded-full bg-sand px-3 py-1 text-xs text-ink/70">{item.event_type}</span>
            </div>
          </article>
        ))}
      </div>
    </SectionCard>
  );
}
