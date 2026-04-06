from models.reservation import Reservation


def format_reservation(res: Reservation) -> str:
    """予約データからフォーマット済み確認書テキストを生成する"""
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("   BETRANK TOURS 予約確認書")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    # 場所
    if res.location:
        lines.append(f"場所: {res.location}")
        lines.append("")

    # ゲスト情報
    lines.append("【ゲスト情報】")
    if res.guests:
        for i, g in enumerate(res.guests, 1):
            lines.append(f"  {i}. {g.passport_name}")
            if g.passport_number:
                lines.append(f"     パスポート: {g.passport_number}")
            if g.passport_expiry:
                lines.append(f"     有効期限: {g.passport_expiry}")
            if g.date_of_birth:
                lines.append(f"     生年月日: {g.date_of_birth}")
    else:
        lines.append("  （未登録）")
    lines.append("")

    # 宿泊情報
    lines.append("【宿泊情報】")
    if res.hotel_name:
        lines.append(f"  ホテル: {res.hotel_name}")
    lines.append(f"  客室: {res.room_type or '未定'}")
    lines.append(f"  部屋数: {res.num_rooms}室")
    if res.check_in and res.check_out:
        nights_str = f"（{res.nights}泊）" if res.nights else ""
        lines.append(f"  期間: {res.check_in} 〜 {res.check_out} {nights_str}")
    lines.append("")

    # 送迎
    lines.append("【送迎】")
    lines.append(f"  {res.transfer_needed or '未定'}")
    lines.append("")

    # バイイン
    lines.append("【バイイン】")
    if res.guests and res.buyin_per_person:
        for g in res.guests:
            name = g.passport_name.split()[0] if g.passport_name else "ゲスト"
            lines.append(f"  {name}様: {res.buyin_per_person}")
        if res.buyin_total:
            lines.append(f"  合計: {res.buyin_total}")
    elif res.buyin_total:
        lines.append(f"  合計: {res.buyin_total}")
    lines.append("")

    # 会員情報
    lines.append("【会員情報】")
    lines.append(f"  グレード: {res.member_grade or '未定'}")
    lines.append(f"  クライアントレベル: {res.client_level or '不明'}")
    lines.append("")

    # フライト情報
    lines.append("【フライト情報】")
    if res.flights:
        outbound = [f for f in res.flights if "往" in f.direction]
        inbound = [f for f in res.flights if "復" in f.direction]
        other = [f for f in res.flights if "往" not in f.direction and "復" not in f.direction]

        for label, flist in [("往路", outbound), ("復路", inbound), ("", other)]:
            for f in flist:
                prefix = f"  {label} " if label else "  "
                lines.append(f"{prefix}{f.departure_date}")
                lines.append(f"    {f.airline}  {f.flight_number}")
                lines.append(f"    {f.departure_airport} {f.departure_time} → {f.arrival_airport} {f.arrival_time}")
                lines.append("")
    else:
        lines.append("  （未登録）")
        lines.append("")

    # プレイ条件
    lines.append("【プレイ条件】")
    if res.buyin_per_person:
        lines.append(f"  バイイン: {res.buyin_per_person}")
    if res.minimum_bet:
        lines.append(f"  ミニマムベット: {res.minimum_bet}")
    if res.total_rolling:
        lines.append(f"  条件ローリング: {res.total_rolling}")
    lines.append("")

    # 費用
    lines.append("【費用】")
    cost_lines = []
    if res.hotel_cost:
        by = f"（{res.hotel_cost_by}）" if res.hotel_cost_by else ""
        cost_lines.append(f"  ホテル: {res.hotel_cost} {by}")
    if res.flight_cost:
        by = f"（{res.flight_cost_by}）" if res.flight_cost_by else ""
        cost_lines.append(f"  フライト: {res.flight_cost} {by}")
    if res.cashback:
        cost_lines.append(f"  キャッシュバック: {res.cashback}")
    if res.local_settlement:
        cost_lines.append(f"  現地精算: {res.local_settlement}")
    if cost_lines:
        lines.extend(cost_lines)
    else:
        lines.append("  （未登録）")
    lines.append("")

    # メモ
    if res.memo:
        lines.append("【メモ】")
        for memo_line in res.memo.split("\n"):
            memo_line = memo_line.strip()
            if memo_line:
                if not memo_line.startswith("・") and not memo_line.startswith("-"):
                    memo_line = f"・{memo_line}"
                lines.append(f"  {memo_line}")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")

    return "\n".join(lines)
