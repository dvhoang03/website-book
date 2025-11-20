# postgres/Dockerfile

# Vẫn sử dụng image bookworm để đảm bảo môi trường ổn định
FROM postgres:16-bookworm

# Cài đặt các gói cần thiết để biên dịch extension
# - git: để lấy mã nguồn
# - build-essential: chứa gcc, make và các công cụ biên dịch cơ bản
# - postgresql-server-dev-all: chứa các file header cần thiết để build extension cho PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    postgresql-server-dev-all \
    && rm -rf /var/lib/apt/lists/*

# Lấy mã nguồn pgvector từ GitHub
# Chúng ta sẽ clone một phiên bản cụ thể (v0.5.1) để đảm bảo tính ổn định
RUN git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git /tmp/pgvector

# Di chuyển vào thư mục mã nguồn
WORKDIR /tmp/pgvector

# Biên dịch mã nguồn
RUN make

# Cài đặt extension vào hệ thống PostgreSQL
RUN make install

# Dọn dẹp thư mục tạm để giảm kích thước image
RUN rm -rf /tmp/pgvector