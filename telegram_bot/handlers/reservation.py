import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from models.reservation import Reservation, GuestInfo, FlightInfo
from services.ocr_passport import extract_passport_info
from services.ocr_ticket import extract_ticket_info
from services.parse_details import parse_reservation_text
from services.formatter import format_reservation

logger = logging.getLogger(__name__)

# 会話ステート
PASSPORT, TICKET, DETAILS, CONFIRM = range(4)

# --- ヘルパー ---

def _get_reservation(context: ContextTypes.DEFAULT_TYPE) -> Reservation:
    if "reservation" not in context.user_data:
        context.user_data["reservation"] = Reservation()
    return context.user_data["reservation"]


def _get_media_type(file_path: str) -> str:
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else "jpg"
    return {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }.get(ext, "image/jpeg")


# --- ハンドラー ---

async def start_reservation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """予約作成を開始する"""
    context.user_data.clear()
    _get_reservation(context)

    await update.message.reply_text(
        "予約確認書を作成します。\n\n"
        "まず、ゲストのパスポート写真を送ってください。\n"
        "複数名の場合は1枚ずつ送ってください。\n\n"
        "全員分送り終わったら /next と入力してください。\n"
        "パスポート写真がない場合は /skip で飛ばせます。"
    )
    return PASSPORT


async def receive_passport_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """パスポート写真を受信してOCR処理する"""
    res = _get_reservation(context)
    photo = update.message.photo[-1]  # 最大解像度

    await update.message.reply_text("パスポートを読み取り中...")

    try:
        file = await photo.get_file()
        image_bytes = await file.download_as_bytearray()
        media_type = _get_media_type(file.file_path or "photo.jpg")

        guest = extract_passport_info(bytes(image_bytes), media_type)
        res.guests.append(guest)

        await update.message.reply_text(
            f"読み取り完了:\n"
            f"  氏名: {guest.passport_name}\n"
            f"  パスポート番号: {guest.passport_number}\n"
            f"  有効期限: {guest.passport_expiry}\n\n"
            f"現在 {len(res.guests)}名登録済み。\n"
            f"次のパスポートを送るか、/next で次のステップへ。"
        )
    except Exception as e:
        logger.error(f"パスポートOCRエラー: {e}")
        await update.message.reply_text(
            "読み取りに失敗しました。再度撮影して送ってください。"
        )

    return PASSPORT


async def skip_passport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """パスポートステップをスキップ"""
    await update.message.reply_text(
        "パスポートをスキップしました。\n\n"
        "次に、航空券（フライト情報）の写真を送ってください。\n"
        "往路・復路を1枚ずつ送ってください。\n\n"
        "全て送り終わったら /next と入力してください。\n"
        "写真がない場合は /skip で飛ばせます。"
    )
    return TICKET


async def next_to_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """パスポート → 航空券ステップへ遷移"""
    res = _get_reservation(context)
    count = len(res.guests)

    await update.message.reply_text(
        f"ゲスト {count}名の登録完了。\n\n"
        "次に、航空券（フライト情報）の写真を送ってください。\n"
        "往路・復路を1枚ずつ送ってください。\n\n"
        "全て送り終わったら /next と入力してください。\n"
        "写真がない場合は /skip で飛ばせます。"
    )
    return TICKET


async def receive_ticket_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """航空券写真を受信してOCR処理する"""
    res = _get_reservation(context)
    photo = update.message.photo[-1]

    await update.message.reply_text("航空券を読み取り中...")

    try:
        file = await photo.get_file()
        image_bytes = await file.download_as_bytearray()
        media_type = _get_media_type(file.file_path or "photo.jpg")

        flights = extract_ticket_info(bytes(image_bytes), media_type)
        res.flights.extend(flights)

        flight_texts = []
        for f in flights:
            flight_texts.append(
                f"  {f.direction} {f.departure_date}\n"
                f"    {f.airline} {f.flight_number}\n"
                f"    {f.departure_airport} {f.departure_time} → {f.arrival_airport} {f.arrival_time}"
            )

        await update.message.reply_text(
            f"読み取り完了:\n" +
            "\n".join(flight_texts) + "\n\n"
            f"合計 {len(res.flights)}フライト登録済み。\n"
            f"次の航空券を送るか、/next で次のステップへ。"
        )
    except Exception as e:
        logger.error(f"航空券OCRエラー: {e}")
        await update.message.reply_text(
            "読み取りに失敗しました。再度撮影して送ってください。"
        )

    return TICKET


async def skip_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """航空券ステップをスキップ"""
    await update.message.reply_text(
        "航空券をスキップしました。\n\n"
        "最後に、予約内容のテキストを送ってください。\n"
        "（ホテル、バイイン、プレイ条件、メモなど全てまとめて）"
    )
    return DETAILS


async def next_to_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """航空券 → テキスト詳細ステップへ遷移"""
    res = _get_reservation(context)
    count = len(res.flights)

    await update.message.reply_text(
        f"フライト {count}件の登録完了。\n\n"
        "最後に、予約内容のテキストを送ってください。\n"
        "（ホテル、バイイン、プレイ条件、メモなど全てまとめて）\n\n"
        "テキストがない場合は /skip で飛ばせます。"
    )
    return DETAILS


async def receive_details_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """予約テキストを受信して解析する"""
    res = _get_reservation(context)
    text = update.message.text

    await update.message.reply_text("テキストを解析中...")

    try:
        data = parse_reservation_text(text)

        # 解析結果をReservationに反映
        res.location = data.get("location", "") or res.location
        res.hotel_name = data.get("hotel_name", "") or res.hotel_name
        res.room_type = data.get("room_type", "") or res.room_type
        res.num_rooms = data.get("num_rooms", 1) or res.num_rooms
        res.check_in = data.get("check_in", "") or res.check_in
        res.check_out = data.get("check_out", "") or res.check_out
        res.nights = data.get("nights", 0) or res.nights
        res.buyin_per_person = data.get("buyin_per_person", "") or res.buyin_per_person
        res.buyin_total = data.get("buyin_total", "") or res.buyin_total
        res.minimum_bet = data.get("minimum_bet", "") or res.minimum_bet
        res.total_rolling = data.get("total_rolling", "") or res.total_rolling
        res.transfer_needed = data.get("transfer_needed", "") or res.transfer_needed
        res.member_grade = data.get("member_grade", "") or res.member_grade
        res.client_level = data.get("client_level", "") or res.client_level
        res.hotel_cost = data.get("hotel_cost", "") or res.hotel_cost
        res.hotel_cost_by = data.get("hotel_cost_by", "") or res.hotel_cost_by
        res.flight_cost = data.get("flight_cost", "") or res.flight_cost
        res.flight_cost_by = data.get("flight_cost_by", "") or res.flight_cost_by
        res.cashback = data.get("cashback", "") or res.cashback
        res.local_settlement = data.get("local_settlement", "") or res.local_settlement
        res.memo = data.get("memo", "") or res.memo

        # テキストからゲスト名も拾う（パスポート写真が無い場合のフォールバック）
        # ゲスト名がテキストに含まれていてパスポートから取得していない場合
        # parse_detailsは名前を返さないのでここでは処理しない

    except Exception as e:
        logger.error(f"テキスト解析エラー: {e}")
        await update.message.reply_text(
            "テキストの解析に失敗しました。もう一度送ってください。"
        )
        return DETAILS

    # 確認書を生成して表示
    confirmation = format_reservation(res)

    keyboard = [
        [
            InlineKeyboardButton("確定", callback_data="confirm"),
            InlineKeyboardButton("修正", callback_data="edit"),
        ],
        [InlineKeyboardButton("キャンセル", callback_data="cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"以下の内容で確認書を作成しました:\n\n{confirmation}",
        reply_markup=reply_markup,
    )
    return CONFIRM


async def skip_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """テキスト詳細をスキップして確認へ"""
    res = _get_reservation(context)
    confirmation = format_reservation(res)

    keyboard = [
        [
            InlineKeyboardButton("確定", callback_data="confirm"),
            InlineKeyboardButton("修正", callback_data="edit"),
        ],
        [InlineKeyboardButton("キャンセル", callback_data="cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"以下の内容で確認書を作成しました:\n\n{confirmation}",
        reply_markup=reply_markup,
    )
    return CONFIRM


async def handle_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """確認画面のボタン処理"""
    query = update.callback_query
    await query.answer()

    if query.data == "confirm":
        res = _get_reservation(context)
        confirmation = format_reservation(res)

        await query.edit_message_text(
            f"予約確認書が確定されました。\n\n{confirmation}\n\n"
            "コピーしてご利用ください。\n"
            "新しい予約を作成するには /reserve と入力してください。"
        )
        context.user_data.clear()
        return ConversationHandler.END

    elif query.data == "edit":
        await query.edit_message_text(
            "修正したい項目を選んでください:\n\n"
            "1. /passport - パスポート写真を再送\n"
            "2. /ticket - 航空券写真を再送\n"
            "3. /details - 予約テキストを再送\n\n"
            "または修正テキストをそのまま送ってください。"
        )
        return DETAILS

    elif query.data == "cancel":
        await query.edit_message_text("予約作成をキャンセルしました。")
        context.user_data.clear()
        return ConversationHandler.END

    return CONFIRM


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """予約作成をキャンセルする"""
    context.user_data.clear()
    await update.message.reply_text(
        "予約作成をキャンセルしました。\n"
        "新しい予約を作成するには /reserve と入力してください。"
    )
    return ConversationHandler.END


def create_reservation_handler() -> ConversationHandler:
    """ConversationHandlerを構築する"""
    return ConversationHandler(
        entry_points=[
            CommandHandler("reserve", start_reservation),
            CommandHandler("start", start_reservation),
        ],
        states={
            PASSPORT: [
                MessageHandler(filters.PHOTO, receive_passport_photo),
                CommandHandler("next", next_to_ticket),
                CommandHandler("skip", skip_passport),
            ],
            TICKET: [
                MessageHandler(filters.PHOTO, receive_ticket_photo),
                CommandHandler("next", next_to_details),
                CommandHandler("skip", skip_ticket),
            ],
            DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_details_text),
                CommandHandler("skip", skip_details),
                CommandHandler("passport", start_reservation),
            ],
            CONFIRM: [
                CallbackQueryHandler(handle_confirm_callback),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
        ],
        conversation_timeout=3600,
    )
