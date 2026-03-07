import SectionCard from "./SectionCard";

export default function CameraFeeds({ cameras = [] }) {
  return (
    <SectionCard title="Camerafeeds" kicker="Lokale alerts">
      <div className="grid gap-4 xl:grid-cols-2">
        {cameras.length === 0 ? (
          <div className="rounded-[24px] bg-white/75 p-5 text-sm text-ink/70">
            Nog geen camera's geconfigureerd. Voeg een camera toe in `config/devices.yaml` of gebruik `config/devices.example.yaml`
            als startpunt.
          </div>
        ) : (
          cameras.map((camera) => (
            <article key={camera.id} className="overflow-hidden rounded-[24px] bg-ink text-white shadow-sm">
              <img
                src={`/api/cameras/${camera.id}/snapshot`}
                alt={camera.name}
                className="h-48 w-full object-cover opacity-90"
              />
              <div className="space-y-2 px-5 py-4">
                <div className="flex items-center justify-between gap-4">
                  <h3 className="text-lg font-medium">{camera.name}</h3>
                  <span className="rounded-full bg-white/10 px-3 py-1 text-xs uppercase tracking-[0.2em]">
                    {camera.status}
                  </span>
                </div>
                <p className="text-sm text-white/70">Laatste alert: {camera.state.last_alert || "Geen meldingen"}</p>
                {camera.state.stream_url ? (
                  <p className="text-sm text-white/60 break-all">Stream: {camera.state.stream_url}</p>
                ) : null}
                <p className="text-xs uppercase tracking-[0.25em] text-white/40">
                  Opname {camera.state.recording ? "actief" : "uitgeschakeld"} · lokale opslag
                </p>
              </div>
            </article>
          ))
        )}
      </div>
    </SectionCard>
  );
}
