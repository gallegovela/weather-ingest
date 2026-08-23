# Imagen del frontend del panel de control (SPA React servida como
# estáticos). Ver spec/control/core.md, "Despliegue": contenedorizado
# con Docker, como servicio nuevo en el docker-compose.yml de la raíz
# del proyecto. El enrutado hacia /api (proxy al contenedor
# control-backend) lo resuelve el nginx externo del servidor de
# destino, fuera del alcance de este proyecto — este contenedor solo
# sirve los ficheros estáticos del build.

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
