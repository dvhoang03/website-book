import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage

# Load biến môi trường
load_dotenv()
app = FastAPI()

# 1. Cấu hình Database & AI
db_uri = os.getenv("DATABASE_URL")
db = SQLDatabase.from_uri(db_uri, sample_rows_in_table_info=0)
api_key = os.getenv("GOOGLE_API_KEY")
engine = create_engine(db_uri)

# Model chính
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=api_key,
    temperature=0,
    convert_system_message_to_human=True
)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=api_key,
    task_type="retrieval_query"
)

class ChatRequest(BaseModel):
    question: str
    session_id: str

# ==============================================================================
# MODULE: QUẢN LÝ LỊCH SỬ CHAT (MEMORY)
# ==============================================================================
def get_chat_history(session_id: str, limit=6):
    """Lấy 6 tin nhắn gần nhất từ bảng chat_messages"""
    try:
        with engine.connect() as conn:
            # Giả sử bảng chat_messages có cột: role (user/bot), content, conversationId (session_id)
            # Bạn cần điều chỉnh câu query này khớp với tên cột thực tế trong DB NestJS của bạn
            query = text(f"""
                SELECT role, content 
                FROM chat_messages 
                WHERE "conversationId" = :session_id 
                ORDER BY "created_at" DESC LIMIT :limit
            """)
            result = conn.execute(query, {"session_id": session_id, "limit": limit}).fetchall()
            
            messages = []
            # Đảo ngược lại để đúng thứ tự thời gian (Cũ -> Mới)
            for row in reversed(result):
                if row[0] == 'user':
                    messages.append(HumanMessage(content=row[1]))
                else:
                    messages.append(AIMessage(content=row[1]))
            return messages
    except Exception as e:
        print(f"⚠️ Lỗi lấy lịch sử: {e}")
        return []

def save_chat_message(session_id: str, role: str, content: str):
    """Lưu tin nhắn vào DB (NestJS Backend thường làm việc này, nhưng Python cũng có thể lưu phụ)"""
    # Trong kiến trúc Microservice của bạn, tốt nhất là để NestJS lưu message trước khi gọi Python.
    # Hàm này để demo logic thôi.
    pass 

# ==============================================================================
# CÔNG CỤ 1: ROUTER (PHÂN LOẠI CÂU HỎI - CÓ CONTEXT)
# ==============================================================================
def route_question(question: str, history: list):
    # Chuyển history thành text để Router hiểu ngữ cảnh
    history_text = "\n".join([f"{m.type}: {m.content}" for m in history])
    
    prompt = ChatPromptTemplate.from_template("""
    Lịch sử trò chuyện:
    {history}
    
    Câu hỏi hiện tại: {question}
    
    Hãy phân loại câu hỏi vào 1 trong 3 loại:
    1. "DATABASE": Hỏi về thông tin sách (giá, tác giả, số lượng, liệt kê).
    2. "POLICY": Hỏi chính sách chung (đổi trả, giao hàng).
    3. "CHITCHAT": Chào hỏi, cảm ơn, hoặc nói chuyện tiếp nối lịch sử mà không cần tra cứu.
    
    Chỉ trả về đúng 1 từ: DATABASE hoặc POLICY hoặc CHITCHAT.
    """)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"question": question, "history": history_text}).strip()

# ==============================================================================
# CÔNG CỤ 2: XỬ LÝ DATABASE
# ==============================================================================
def handle_database_query(question: str, history: list):
    history_text = "\n".join([f"{m.type}: {m.content}" for m in history])
    
    # Bước 1: Viết SQL (Có tham khảo lịch sử để hiểu từ "nó", "cuốn đó")
    sql_prompt = ChatPromptTemplate.from_template("""
    Bạn là chuyên gia SQL.
    Lịch sử: {history}
    Câu hỏi: {question}
    
    Schema: {schema}
    
    Nhiệm vụ: Viết câu lệnh PostgreSQL query.
    Lưu ý: 
    - Nếu câu hỏi là "giá bao nhiêu", hãy tìm giá của cuốn sách được nhắc đến gần nhất trong lịch sử.
    - Dùng ILIKE cho tên sách. Tên bảng trong ngoặc kép.
    - Chỉ trả về SQL.
    """)
    
    schema_info = db.get_table_info(['books', 'authors'])
    sql_chain = sql_prompt | llm | StrOutputParser()
    generated_sql = sql_chain.invoke({"question": question, "history": history_text, "schema": schema_info})
    
    cleaned_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
    print(f"Generated SQL: {cleaned_sql}")

    # Bước 2: Chạy SQL
    try:
        with engine.connect() as conn:
            # Chặn các lệnh nguy hiểm
            if "DROP" in cleaned_sql.upper() or "DELETE" in cleaned_sql.upper():
                return "Tôi không được phép thực hiện lệnh này."
                
            result = conn.execute(text(cleaned_sql)).fetchall()
            if not result:
                return "Xin lỗi, không tìm thấy dữ liệu phù hợp."
            
            # Bước 3: Trả lời tự nhiên
            final_prompt = ChatPromptTemplate.from_template("""
            Câu hỏi: {question}
            Kết quả DB: {result}
            
            Hãy trả lời câu hỏi dựa trên kết quả DB. Giọng điệu thân thiện nhân viên bán hàng.
            """)
            chain = final_prompt | llm | StrOutputParser()
            return chain.invoke({"question": question, "result": str(result)})
            
    except Exception as e:
        print(f"SQL Error: {e}")
        return "Xin lỗi, hệ thống không tìm thấy thông tin."

# ==============================================================================
# CÔNG CỤ 3: XỬ LÝ CHÍNH SÁCH
# ==============================================================================
def handle_policy_query(question: str):
    try:
        vector = embeddings.embed_query(question)
        with engine.connect() as conn:
            query = text("""
                SELECT content, 1 - (embedding <=> CAST(:vector AS vector)) as similarity 
                FROM policies 
                ORDER BY similarity DESC LIMIT 1
            """)
            row = conn.execute(query, {"vector": str(vector)}).fetchone()
            
            if row and row[1] > 0.3:
                return row[0] # Trả về nội dung policy
            else:
                return "Xin lỗi, tôi không tìm thấy chính sách liên quan."
    except Exception:
        return "Đang bảo trì tính năng tra cứu."

# ==============================================================================
# API ENDPOINT
# ==============================================================================
@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    print(f"\n💬 User asking: {req.question}")
    
    # 1. Lấy lịch sử chat từ DB (Quan trọng!)
    history = get_chat_history(req.session_id)
    
    # 2. Phân loại câu hỏi
    intent = route_question(req.question, history)
    print(f"👉 Intent: {intent}")
    
    response = ""
    source = "ai"
    
    if intent == "DATABASE":
        response = handle_database_query(req.question, history)
        source = "database"
    elif intent == "POLICY":
        response = handle_policy_query(req.question)
        source = "policy"
    else:
        # Chitchat: Trả lời dựa trên lịch sử
        prompt = ChatPromptTemplate.from_template("""
        Lịch sử: {history}
        Người dùng: {question}
        Hãy trả lời thân thiện, ngắn gọn.
        """)
        chain = prompt | llm | StrOutputParser()
        response = chain.invoke({"history": history, "question": req.question})
        source = "chitchat"

    return {"source": source, "content": response}