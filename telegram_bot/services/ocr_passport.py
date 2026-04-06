import json
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from models.reservation import GuestInfo

PASSPORT_PROMPT = """あなたはパスポート写真のOCR専門家です。
送られたパスポート写真から以下の情報を抽出してください。

必ず以下のJSON形式のみを返してください。他のテキストは一切不要です。

{
    "passport_name": "姓 名（ローマ字大文字、パスポート記載通り）",
    "passport_number": "パスポート番号",
    "passport_expiry": "YYYY/MM/DD",
    "nationality": "国籍（日本語）",
    "date_of_birth": "YYYY/MM/DD",
    "gender": "M または F"
}

MRZ（機械読取領域）が見える場合は、視覚的に読み取った情報と照合して精度を高めてください。
読み取れないフィールドは空文字 "" にしてください。"""


def extract_passport_info(image_bytes: bytes, media_type: str = "image/jpeg") -> GuestInfo:
    """パスポート写真からゲスト情報を抽出する"""
    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            genai.types.Part.from_bytes(data=image_bytes, mime_type=media_type),
            PASSPORT_PROMPT,
        ],
    )

    raw = response.text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)

    return GuestInfo(
        passport_name=data.get("passport_name", ""),
        passport_number=data.get("passport_number", ""),
        passport_expiry=data.get("passport_expiry", ""),
        nationality=data.get("nationality", ""),
        date_of_birth=data.get("date_of_birth", ""),
        gender=data.get("gender", ""),
    )
