export default function SectionCard({ title, kicker, actions, className = "", children }) {
  return (
    <section className={`glass-panel ${className}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-ink/40">{kicker}</p>
          <h2 className="mt-2 text-xl font-semibold text-ink">{title}</h2>
        </div>
        {actions ? <div>{actions}</div> : null}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}
