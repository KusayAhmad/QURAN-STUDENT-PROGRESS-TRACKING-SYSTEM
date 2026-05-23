async function getApiHealth(): Promise<{ status: string; env?: string } | null> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${apiUrl}/health`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as { status: string; env?: string };
  } catch {
    return null;
  }
}

export default async function Home() {
  const health = await getApiHealth();
  return (
    <main style={{ padding: "2rem", maxWidth: 720, margin: "0 auto" }}>
      <h1>Quran Student Progress Tracking</h1>
      <p style={{ color: "#555" }}>
        MVP-1 frontend skeleton. Auth, student management, and the memorization
        matrix UI will be built on top of this.
      </p>

      <section style={{ marginTop: "2rem" }}>
        <h2>Backend status</h2>
        {health ? (
          <pre
            style={{
              background: "#f4f4f4",
              padding: "1rem",
              borderRadius: 8,
            }}
          >
            {JSON.stringify(health, null, 2)}
          </pre>
        ) : (
          <p style={{ color: "#b00" }}>
            API not reachable. Set <code>NEXT_PUBLIC_API_URL</code> or start the
            backend on port 8000.
          </p>
        )}
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2>Useful links</h2>
        <ul>
          <li>
            <a href="http://localhost:8000/docs">API docs (Swagger)</a>
          </li>
          <li>
            <a href="http://localhost:8000/redoc">API docs (ReDoc)</a>
          </li>
        </ul>
      </section>
    </main>
  );
}
