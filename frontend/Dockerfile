# ----------- STAGE: dev -----------
FROM node:20-bullseye AS dev
WORKDIR /app

# Copie les fichiers de dépendances
COPY pnpm-lock.yaml package.json ./

# Installe PNPM et les dépendances sans copier le reste du projet
RUN npm install -g pnpm \
    && pnpm install --frozen-lockfile

# Copie le reste du code (sauf node_modules, ignoré grâce au .dockerignore)
COPY . .

EXPOSE 5173
CMD ["pnpm", "run", "dev", "--", "--host", "0.0.0.0"]
