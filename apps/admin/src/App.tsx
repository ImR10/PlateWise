export default function App() {
  return (
    <main className="shell">
      <header className="shell-header">
        <h1>PlateWise Admin</h1>
        <p className="shell-subtitle">Dining-hall staff console</p>
      </header>
      <section className="shell-body" aria-label="Application status">
        <p className="shell-status">
          <span className="shell-status-dot" aria-hidden="true" />
          Application shell running
        </p>
        <p className="shell-note">
          This is the desktop application boundary foundation. Catalog
          management, import review, and API integration arrive in later
          milestones.
        </p>
      </section>
    </main>
  );
}
