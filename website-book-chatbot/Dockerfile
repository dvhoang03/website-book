    # 1. Sử dụng Python 3.10 bản nhẹ (slim)
    FROM python:3.10-slim

    # 2. Thiết lập biến môi trường
    # PYTHONDONTWRITEBYTECODE: Ngăn Python tạo file .pyc
    # PYTHONUNBUFFERED: In log ra console ngay lập tức (dễ debug)
    ENV PYTHONDONTWRITEBYTECODE=1
    ENV PYTHONUNBUFFERED=1

    # 3. Thiết lập thư mục làm việc
    WORKDIR /app

    # 4. Cài đặt các gói hệ thống cần thiết
    # build-essential & libpq-dev: Cần thiết để thư viện psycopg2 kết nối được PostgreSQL
    RUN apt-get update && apt-get install -y \
        build-essential \
        libpq-dev \
        gcc \
        && rm -rf /var/lib/apt/lists/*

    # 5. Copy file requirements và cài đặt thư viện Python
    # (Copy riêng bước này để tận dụng Docker Cache, giúp build nhanh hơn nếu code đổi nhưng thư viện không đổi)
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    # 6. Copy toàn bộ code vào container
    COPY . .

    # 7. Mở cổng 8000
    EXPOSE 8000

    # 8. Lệnh khởi chạy server
    CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]