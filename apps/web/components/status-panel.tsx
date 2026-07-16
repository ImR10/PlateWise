import type { ApiStatusResult } from "@/lib/api";

export function StatusPanel({ result }: { result: ApiStatusResult }) {
  const connected = result.connected;

  return (
    <section className="rounded-3xl border border-emerald-950/10 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold tracking-[0.22em] text-emerald-800 uppercase">
            Development status
          </p>
          <h2 className="mt-2 text-2xl font-semibold">Backend connection</h2>
        </div>
        <span
          className={`h-3 w-3 rounded-full ${connected ? "bg-emerald-500" : "bg-amber-500"}`}
          aria-label={connected ? "Connected" : "Unavailable"}
        />
      </div>
      <p className="mt-6 text-lg font-medium">
        {connected ? "API connected" : "API unavailable"}
      </p>
      <p className="mt-1 text-sm leading-6 text-slate-600">
        {connected
          ? `${result.data.service} is running in ${result.data.environment} mode.`
          : result.message}
      </p>
    </section>
  );
}
