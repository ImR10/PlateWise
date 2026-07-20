FROM node:22-alpine

ENV PNPM_HOME=/pnpm \
    PATH=/pnpm:$PATH \
    NEXT_TELEMETRY_DISABLED=1

RUN corepack enable && corepack prepare pnpm@11.13.1 --activate

WORKDIR /workspace

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/user/package.json apps/user/package.json
# The admin app shares this pnpm workspace; its manifest must be present for a
# frozen-lockfile install even though the admin app itself is never built here.
COPY apps/admin/package.json apps/admin/package.json
RUN pnpm install --frozen-lockfile

COPY apps/user apps/user

EXPOSE 3000

CMD ["pnpm", "--filter", "@platewise/user", "dev", "--hostname", "0.0.0.0"]
