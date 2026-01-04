# --- GIAI ĐOẠN 1: Build Code (Dùng Node) ---
FROM node:18-alpine as build-stage

# Tạo thư mục làm việc
WORKDIR /app

# Copy package.json vào trước để cài thư viện (tận dụng cache)
COPY package*.json ./
RUN npm install

# Copy toàn bộ code vào và Build
COPY . .
RUN npm run build

# --- GIAI ĐOẠN 2: Chạy Web (Dùng Nginx) ---
FROM nginx:stable-alpine as production-stage

# Copy file đã build từ giai đoạn 1 sang thư mục của Nginx
# Lưu ý: Vite build ra thư mục 'dist', nếu dùng Create-React-App thì sửa thành 'build'
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy file cấu hình Nginx mình vừa tạo vào
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Mở cổng 80
EXPOSE 80

# Chạy Nginx
CMD ["nginx", "-g", "daemon off;"]