import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ Lỗi: Không tìm thấy GOOGLE_API_KEY trong file .env")
    exit()

genai.configure(api_key=api_key)

print(f"🔑 Đang kiểm tra API Key: {api_key[:5]}...{api_key[-5:]}")

try:
    print("\n📡 Đang lấy danh sách Model từ Google...")
    models = genai.list_models()
    
    available_models = []
    print("\n✅ DANH SÁCH MODEL KHẢ DỤNG CHO BẠN:")
    for m in models:
        # Chỉ lấy các model hỗ trợ generateContent (Chat)
        if 'generateContent' in m.supported_generation_methods:
            print(f"   - {m.name}")
            available_models.append(m.name)

    if not available_models:
        print("\n⚠️ CẢNH BÁO: API Key này không tìm thấy model chat nào!")
        print("👉 Hãy truy cập https://aistudio.google.com/app/apikey để tạo Key mới.")
    else:
        print(f"\n💡 GỢI Ý: Hãy dùng tên model chính xác ở trên (bỏ chữ 'models/' đi) để điền vào file main.py")
        print(f"   Ví dụ: Nếu thấy 'models/gemini-1.5-flash', hãy điền 'gemini-1.5-flash'")

except Exception as e:
    print(f"\n❌ LỖI KẾT NỐI: {e}")
    print("👉 Kiểm tra lại Internet hoặc xem API Key có bị disable không.")