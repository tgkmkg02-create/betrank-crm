import json
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from models.reservation import FlightInfo

TICKET_PROMPT = """あなたは航空券・搭乗券写真のOCR専門家です。
送られた写真からフライト情報を抽出してください。

必ず以下のJSON配列形式のみを返してください。他のテキストは一切不要です。
複数のフライト区間が見える場合は配列に複数要素を入れてください。

[
    {
        "direction": "往路 または 復路（日本の空港が出発なら往路、到着なら復路）",
        "airline": "航空会社名（日本語。例: チェジュ航空、大韓航空、アシアナ航空）",
        "flight_number": "便名（例: 7C1306）",
        "departure_airport": "出発空港IATAコード（例: KIX）",
        "arrival_airport": "到着空港IATAコード（例: ICN）",
        "departure_date": "出発日 M/DD形式（例: 4/27）",
        "departure_time": "出発時刻 HH:MM形式（例: 13:35）",
        "arrival_time": "到着時刻 HH:MM形式（例: 15:35）"
    }
]

読み取れないフィールドは空文字 "" にしてください。"""


def extract_ticket_info(image_bytes: bytes, media_type: str = "image/jpeg") -> list[FlightInfo]:
    """航空券写真からフライト情報を抽出する"""
    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            genai.types.Part.from_bytes(data=image_bytes, mime_type=media_type),
            TICKET_PROMPT,
        ],
    )

    raw = response.text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)
    if isinstance(data, dict):
        data = [data]

    flights = []
    for item in data:
        flights.append(FlightInfo(
            direction=item.get("direction", ""),
            airline=item.get("airline", ""),
            flight_number=item.get("flight_number", ""),
            departure_airport=item.get("departure_airport", ""),
            arrival_airport=item.get("arrival_airport", ""),
            departure_date=item.get("departure_date", ""),
            departure_time=item.get("departure_time", ""),
            arrival_time=item.get("arrival_time", ""),
        ))

    return flights
