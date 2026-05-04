FROM node:22-slim

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

RUN corepack enable

WORKDIR /app

COPY package.json pnpm-lock.yaml ./

RUN pnpm install 

COPY . .

EXPOSE 3000

CMD ["pnpm", "dev", "--host"]
