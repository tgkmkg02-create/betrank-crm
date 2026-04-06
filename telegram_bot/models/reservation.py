from dataclasses import dataclass, field


@dataclass
class GuestInfo:
    passport_name: str = ""
    passport_number: str = ""
    passport_expiry: str = ""
    nationality: str = ""
    date_of_birth: str = ""
    gender: str = ""


@dataclass
class FlightInfo:
    direction: str = ""        # 往路 or 復路
    airline: str = ""
    flight_number: str = ""
    departure_airport: str = ""
    arrival_airport: str = ""
    departure_date: str = ""
    departure_time: str = ""
    arrival_time: str = ""


@dataclass
class Reservation:
    # ゲスト
    guests: list[GuestInfo] = field(default_factory=list)

    # フライト
    flights: list[FlightInfo] = field(default_factory=list)

    # ホテル
    location: str = ""
    hotel_name: str = ""
    room_type: str = ""
    num_rooms: int = 1
    check_in: str = ""
    check_out: str = ""
    nights: int = 0

    # カジノ条件
    buyin_per_person: str = ""
    buyin_total: str = ""
    minimum_bet: str = ""
    total_rolling: str = ""

    # サービス
    transfer_needed: str = ""
    member_grade: str = ""
    client_level: str = ""

    # 費用
    hotel_cost: str = ""
    hotel_cost_by: str = ""
    flight_cost: str = ""
    flight_cost_by: str = ""
    cashback: str = ""
    local_settlement: str = ""

    # メモ
    memo: str = ""
