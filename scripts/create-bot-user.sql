-- file: scripts/create-bot-user.sql

DO
$do$
BEGIN
   -- 1. Tạo User nếu chưa có
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'bot_user') THEN
      CREATE ROLE bot_user LOGIN PASSWORD 'SecureBotPass123!';
   END IF;
END
$do$;

-- 2. Cấp quyền kết nối
GRANT CONNECT ON DATABASE "book" TO bot_user; -- Đảm bảo tên DB khớp với .env

-- 3. Cấp quyền Schema
GRANT USAGE ON SCHEMA public TO bot_user;

-- 4. CẤP QUYỀN MẶC ĐỊNH CHO CÁC BẢNG TƯƠNG LAI (Giải quyết triệt để lỗi Race Condition)
-- Ý nghĩa: "Này Postgres, sau này hễ có bảng nào mới được tạo, hãy tự động cấp quyền cho bot_user luôn"
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE ON TABLES TO bot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO bot_user;

-- 5. Cấp quyền cho các bảng ĐÃ TỒN TẠI (Nếu có)
-- Dùng câu lệnh này an toàn hơn, không cần liệt kê tên bảng cụ thể
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO bot_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO bot_user;

-- 6. Đảm bảo an toàn: Thu hồi quyền XÓA (nếu lỡ có cấp)
REVOKE DELETE ON ALL TABLES IN SCHEMA public FROM bot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE DELETE ON TABLES FROM bot_user;