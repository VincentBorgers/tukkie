import SectionCard from "./SectionCard";

export default function RoomsOverview({ rooms = [], scenes = [] }) {
  return (
    <SectionCard title="Ruimtes" kicker="Ruimtes en scènes">
      <div className="grid gap-4 lg:grid-cols-2">
        {rooms.map((room) => (
          <article key={room.id} className="rounded-[24px] bg-white/70 p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-ink">{room.name}</h3>
              <span className="rounded-full bg-moss/20 px-3 py-1 text-xs font-medium text-moss">
                {room.status}
              </span>
            </div>
            <p className="mt-2 text-sm text-ink/70">{room.purpose || "Geen omschrijving"}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {Object.entries(room.metrics || {}).map(([key, value]) => (
                <span key={key} className="rounded-full bg-sand px-3 py-1 text-xs text-ink/75">
                  {key}: {value}
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>

      <div className="mt-5 rounded-[24px] bg-ink px-5 py-4 text-white">
        <p className="text-xs uppercase tracking-[0.3em] text-white/60">Bekende scènes</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {scenes.length === 0 ? (
            <span className="rounded-full border border-white/20 px-3 py-2 text-sm text-white/70">Nog geen scènes geconfigureerd</span>
          ) : (
            scenes.map((scene) => (
              <span key={scene.id} className="rounded-full border border-white/20 px-3 py-2 text-sm text-white/80">
                {scene.name}
              </span>
            ))
          )}
        </div>
      </div>
    </SectionCard>
  );
}
