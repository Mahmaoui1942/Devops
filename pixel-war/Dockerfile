# Stage 1 : Build React
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .
RUN npm run build

# Stage 2 : Serve avec nginx
FROM nginxinc/nginx-unprivileged:alpine

COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose the unprivileged port (8080 as configured in nginx.conf)
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
