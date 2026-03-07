const stats = [
  {
    key: "rooms_online",
    label: "Ruimtes online",
    suffix: ""
  },
  {
    key: "devices_online",
    label: "Devices actief",
    suffix: ""
  },
  {
    key: "lights_on",
    label: "Lampen aan",
    suffix: ""
  },
  {
    key: "automation_count",
    label: "Automatiseringen",
    suffix: ""
  }
];

export default function StatusStrip({ assistant, homeStatus }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {stats.map((item) => (
        <div key={item.key} className="glass-panel !p-5">
          <p className="text-xs uppercase tracking-[0.3em] text-ink/40">{item.label}</p>
          <p className="mt-3 text-3xl font-semibold text-ink">
            {homeStatus?.[item.key] ?? 0}
            {item.suffix}
          </p>
          <p className="mt-3 text-sm text-ink/70">
            {assistant?.name || "Tukkie"} draait lokaal in {assistant?.language || "nl-NL"} modus.
          </p>
        </div>
      ))}
    </div>
  );
}
