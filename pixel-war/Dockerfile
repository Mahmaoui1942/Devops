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

# Automatically replace port 80 with 8080 in your custom nginx config
USER root
RUN sed -i 's/listen  *80;/listen 8080;/g' /etc/nginx/conf.d/default.conf
USER 101

# Expose the correct unprivileged port
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
