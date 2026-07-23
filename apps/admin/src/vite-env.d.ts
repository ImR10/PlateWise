/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** API base URL override for development; defaults to http://localhost:8000. */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
