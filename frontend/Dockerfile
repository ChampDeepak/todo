# syntax=docker/dockerfile:1

# ============================================================================
# Stage 1 -- build. Node, npm and ~200MB of node_modules live here and are
# thrown away at the end of this stage.
# ============================================================================
FROM node:22-alpine AS build

WORKDIR /build

# Dependencies before source, so a code edit reuses the cached npm install.
# `npm ci` (not `npm install`) installs exactly what package-lock.json pins and
# fails if the lockfile is out of sync -- the build must be reproducible.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build          # produces /build/dist

# ============================================================================
# Stage 2 -- runtime. A fresh image. Nothing from stage 1 is present except
# what is explicitly copied across, so Node and node_modules do not ship.
# Result: ~50MB instead of ~1.1GB, and a far smaller CVE surface for M6.
# ============================================================================
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /build/dist /usr/share/nginx/html

# The nginx image ships an `nginx` user (uid 101) but runs its master process
# as root. Give that user ownership of everything it must write, then switch.
RUN touch /tmp/nginx.pid \
    && chown -R nginx:nginx /usr/share/nginx/html /tmp/nginx.pid \
    && chmod -R a+rX /usr/share/nginx/html
USER nginx

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1:8080/ || exit 1

# The base image's entrypoint script writes into root-owned /etc/nginx at
# startup, which fails as uid 101. Bypass it and start nginx directly.
ENTRYPOINT []
CMD ["nginx", "-g", "daemon off;"]
