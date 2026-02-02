# 빌드 스테이지
FROM node:24-alpine AS builder

WORKDIR /app

# package.json과 package-lock.json 복사
COPY package*.json ./

# devDependencies 포함해서 설치 (빌드 시 필요)
RUN npm ci

# 소스 코드 복사
COPY . .

# Vite로 빌드
RUN npm run build

# 프로덕션 스테이지 (Nginx)
FROM nginx:alpine

# 빌드된 dist 폴더를 Nginx로 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx 설정 복사
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
