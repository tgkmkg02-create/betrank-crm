import json
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL

PARSE_PROMPT = """あなたはカジノツアー会社の予約情報解析の専門家です。
オペレーターが送ってきた予約テキストから情報を抽出してJSON形式で返してください。

必ず以下のJSON形式のみを返してください。他のテキストは一切不要です。
該当しない情報は空文字 "" にしてください。

{
    "location": "カジノ・プレイ場所（例: パラダイスシティ、インスパイア）",
    "hotel_name": "ホテル名（場所と同じ場合も記載）",
    "room_type": "客室タイプ（例: Deluxe Twin）",
    "num_rooms": 1,
    "check_in": "チェックイン日（例: 4/27）",
    "check_out": "チェックアウト日（例: 4/28）",
    "nights": 1,
    "buyin_per_person": "1人あたりバイイン額（例: 77万円）",
    "buyin_total": "合計バイイン額（例: 154万円）",
    "minimum_bet": "ミニマムベット（例: 30万ウォン）",
    "total_rolling": "条件ローリング（例: 2千万ウォン）",
    "transfer_needed": "送迎の要否と詳細（例: 必要）",
    "member_grade": "会員グレード（例: 初回、VIP等）",
    "client_level": "クライアントレベル",
    "hotel_cost": "ホテル費用（例: 198000ウォン）",
    "hotel_cost_by": "ホテル費用負担者（例: 弊社、お客様）",
    "flight_cost": "フライト費用（例: 70000円）",
    "flight_cost_by": "フライト費用負担者（例: 弊社、お客様）",
    "cashback": "キャッシュバック額（例: 70000円）",
    "local_settlement": "現地精算の有無と金額",
    "memo": "その他メモ・備考（箇条書きで全て含める）"
}"""


def parse_reservation_text(text: str) -> dict:
    """予約テキストからカジノツアー詳細を解析する"""
    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"{PARSE_PROMPT}\n\n---\n以下が予約テキストです:\n\n{text}",
    )

    raw = response.text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)
