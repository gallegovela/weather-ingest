# Control panel frontend image (React SPA served as static files).
# See spec/control/core.md, "Deployment": containerized with Docker,
# as a new service in the project root's docker-compose.yml. Routing
# to /api (proxy to the control-backend container) is resolved by the
# target server's external nginx, out of this project's scope — this
# container only serves the build's static files.

FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
