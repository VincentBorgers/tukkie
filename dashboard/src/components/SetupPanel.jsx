import SectionCard from "./SectionCard";

export default function SetupPanel({ setup }) {
  const configFiles = setup?.config?.files || [];
  const integrations = setup?.integrations || [];

  return (
    <SectionCard title="Setupstatus" kicker="Runtime en configuratie">
      <div className="space-y-5">
        <div className="grid gap-3 md:grid-cols-2">
          <article className="rounded-[24px] bg-ink px-4 py-4 text-white">
            <p className="text-xs uppercase tracking-[0.28em] text-white/60">Ollama</p>
            <p className="mt-2 text-lg">{setup?.ollama?.available ? "Bereikbaar" : "Niet gevonden"}</p>
            <p className="mt-2 text-sm text-white/70">{setup?.ollama?.host || "Geen host ingesteld"}</p>
          </article>
          <article className="rounded-[24px] bg-white/80 px-4 py-4 text-ink">
            <p className="text-xs uppercase tracking-[0.28em] text-ink/40">Configuratie</p>
            <p className="mt-2 text-lg">{configFiles.filter((file) => file.exists).length}/{configFiles.length} bestanden</p>
            <p className="mt-2 text-sm text-ink/70">Ruimtes, apparaten, scènes en regels komen uit YAML-bestanden in de projectmap.</p>
          </article>
        </div>

        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-ink/40">Bestanden</p>
          <div className="mt-3 space-y-2">
            {configFiles.map((file) => (
              <div key={file.path} className="flex items-center justify-between rounded-2xl bg-white/75 px-4 py-3 text-sm">
                <span className="text-ink/75">{file.name}</span>
                <span className={`status-pill ${file.exists ? "status-pill--ok" : "status-pill--warn"}`}>
                  {file.exists ? "gevonden" : "mist"}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-ink/40">Integraties</p>
          <div className="mt-3 grid gap-3">
            {integrations.map((integration) => (
              <article key={integration.adapter} className="rounded-[22px] bg-white/75 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-medium text-ink">{integration.adapter}</span>
                  <span className={`status-pill ${integration.connected ? "status-pill--ok" : "status-pill--warn"}`}>
                    {integration.mode}
                  </span>
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>
    </SectionCard>
  );
}
