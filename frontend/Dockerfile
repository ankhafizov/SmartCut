FROM node:16 AS builder
ARG SAMPLE_VIDEO_URL
RUN echo SMARTCUT_SAMPLE_VIDEO_URL=$SAMPLE_VIDEO_URL > ./.env
COPY app/package.json app/package-lock.json ./
RUN npm install
COPY app/ ./
RUN npm run build

FROM nginx
COPY --from=builder /dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx","-g","daemon off;"]

