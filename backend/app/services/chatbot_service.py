import json
from pathlib import Path
from typing import List

from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.crud.system import system_setting


def load_synonyms() -> dict:
    try:
        base_path = Path(__file__).resolve().parent.parent
        json_path = base_path / "utils" / "synonyms.json"
        
        if not json_path.exists():
            print(f"Warning: Không tìm thấy file từ điển tại {json_path}")
            return {}
            
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading synonyms: {e}")
        return {}

SYNONYMS = load_synonyms()

def expand_search_query(user_query: str) -> str:
    query_lower = user_query.lower()
    expanded_words = set(query_lower.split())
    
    for main_key, variations in SYNONYMS.items():
        if main_key in query_lower or any(v in query_lower for v in variations):
            expanded_words.add(main_key)
            expanded_words.update(variations)
            
    return " | ".join(expanded_words)

def convert_history_to_gemini(history: List[dict]):
    """
    Chuyển đổi lịch sử chat sang định dạng của Google GenAI SDK v1.0+
    Format: [{'role': 'user'|'model', 'parts': [{'text': '...'}]}]
    """
    gemini_history = []
    for msg in history:
        role = msg.get("role")
        content = msg.get("content")
        
        if role == "system":
            continue
            
        gemini_role = "model" if role == "assistant" else "user"
        
        gemini_history.append({
            "role": gemini_role,
            "parts": [{"text": str(content)}]
        })
    return gemini_history

async def process_chat_message(db: AsyncSession, message: str, history: List[dict]) -> str:
    
    is_active = await system_setting.get_value(db=db, key="chatbot_enabled", default=True)
    if not is_active:
        return "Xin lỗi, tính năng Chatbot tư vấn hiện đang bảo trì để nâng cấp. Bạn vui lòng quay lại sau nhé!"

    product_context = ""
    try:
        search_query = expand_search_query(message)
        
        sql = text("""
            SELECT 
                p.product_name, p.base_price, p.description, c.category_name,
                STRING_AGG(DISTINCT col.color_name, ', ') as available_colors,
                STRING_AGG(DISTINCT s.size_name, ', ') as available_sizes,
                COALESCE(SUM(v.stock_quantity), 0) as total_stock,
                (SELECT image_url FROM product_images pi WHERE pi.product_id = p.product_id AND pi.is_primary = true LIMIT 1) as image
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN product_variants v ON p.product_id = v.product_id
            LEFT JOIN colors col ON v.color_id = col.color_id
            LEFT JOIN sizes s ON v.size_id = s.size_id
            WHERE p.is_active = true AND p.deleted_at IS NULL
            AND to_tsvector('simple', p.product_name || ' ' || COALESCE(p.description, '') || ' ' || COALESCE(c.category_name, '')) @@ to_tsquery('simple', :q)
            GROUP BY p.product_id, c.category_name
            LIMIT 5
        """)
        
        if not search_query.strip():
            result_rows = []
        else:
            result = await db.execute(sql, {"q": search_query})
            result_rows = result.fetchall()

        if not result_rows:
            sql_fallback = text("""
                SELECT p.product_name, p.base_price, p.description, 
                'Đang cập nhật' as available_colors, 'Đang cập nhật' as available_sizes,
                10 as total_stock, '' as image
                FROM products p 
                WHERE p.product_name ILIKE :q AND p.is_active = true LIMIT 3
            """)
            result = await db.execute(sql_fallback, {"q": f"%{message}%"})
            result_rows = result.fetchall()

        if result_rows:
            items = []
            for row in result_rows:
                stock_val = row.total_stock if row.total_stock is not None else 0
                stock_status = f"Còn {stock_val} sp" if stock_val > 0 else "HẾT HÀNG"
                item_info = (
                    f"- {row.product_name} | {row.base_price:,.0f}đ\n"
                    f"  Màu: {row.available_colors} | Size: {row.available_sizes}\n"
                    f"  Tình trạng: {stock_status} | Ảnh: {row.image or 'Không có'}"
                )
                items.append(item_info)
            product_context = "\n".join(items)

    except Exception as e:
        print(f"DB Search Error: {e}")
        product_context = ""

    
    if not product_context:
        sys_instruction = "Bạn là AI tư vấn thời trang StyleX. Khách hỏi món KHÔNG CÓ trong kho. Hãy xin lỗi và gợi ý chung chung."
    else:
        sys_instruction = f"""
        Bạn là Sales Stylist của StyleX. Dữ liệu kho hàng thực tế:
        ---
        {product_context}
        ---
        Yêu cầu:
        1. Tư vấn dựa trên dữ liệu trên.
        2. Báo giá và tình trạng hàng.
        3. Văn phong thân thiện.
        """

    try:
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        
        gemini_history = convert_history_to_gemini(history)
        
        gemini_history.append({
            "role": "user",
            "parts": [{"text": message}]
        })
        
        response = client.models.generate_content(
            model=settings.GOOGLE_MODEL,
            contents=gemini_history,
            config=types.GenerateContentConfig(
                system_instruction=sys_instruction,
                temperature=0.7,
            )
        )
        
        if response.text:
            return response.text
        return "Xin lỗi, mình chưa hiểu ý bạn. Bạn nói lại rõ hơn được không?"
        
    except Exception as e:
        print(f"Gemini AI Error: {e}")
        return "Hệ thống đang bận xíu, bạn chờ chút rồi hỏi lại nhé!"