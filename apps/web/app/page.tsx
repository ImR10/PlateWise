import { StatusPanel } from "@/components/status-panel";
import { getApiStatus } from "@/lib/api";

export default async function Home() {
  const apiStatus = await getApiStatus();

  return (
    <main className="min-h-screen px-6 py-10 sm:px-10 lg:px-16">
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl items-center gap-12 lg:grid-cols-[1.2fr_0.8fr]">
        <section>
          <p className="text-sm font-bold tracking-[0.28em] text-emerald-800 uppercase">
            PlateWise
          </p>
          <h1 className="mt-5 max-w-3xl text-5xl leading-[1.05] font-semibold tracking-tight sm:text-7xl">
            A clearer way to navigate campus dining.
          </h1>
          <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-600">
            This early foundation connects a Next.js interface to a FastAPI
            service and PostgreSQL. Menu ingestion and recommendations come
            next—after the data and safety rules are ready.
          </p>
          <div className="mt-8 inline-flex rounded-full bg-emerald-950 px-4 py-2 text-sm font-medium text-white">
            MVP foundation · no personal profiles collected
          </div>
        </section>

        <StatusPanel result={apiStatus} />
      </div>
    </main>
  );
}
