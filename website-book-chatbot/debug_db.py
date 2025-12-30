import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Lấy chuỗi kết nối từ .env
db_uri = os.getenv("DATABASE_URL")
print(f"🔌 Đang kết nối tới: {db_uri}")

try:
    engine = create_engine(db_uri)
    with engine.connect() as conn:
        # 1. Kiểm tra xem có bảng 'books' không
        print("\n--- KIỂM TRA BẢNG ---")
        result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
        tables = [row[0] for row in result]
        print(f"Các bảng tìm thấy: {tables}")

        if 'books' in tables:
            # 2. Kiểm tra dữ liệu thật trong bảng books
            print("\n--- DỮ LIỆU THẬT TRONG DB ---")
            # Lấy 5 cuốn sách đầu tiên
            books = conn.execute(text('SELECT title FROM "books" LIMIT 5')).fetchall()
            if not books:
                print("⚠️ Bảng 'books' CÓ tồn tại nhưng RỖNG (Không có dữ liệu)!")
            else:
                print(f"Tìm thấy {len(books)} sách mẫu:")
                for b in books:
                    print(f"  - {b[0]}")
        else:
            print("❌ KHÔNG tìm thấy bảng 'books'. Bạn đang kết nối sai Database!")

except Exception as e:
    print(f"❌ Lỗi kết nối: {e}")