import asyncio
import random

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from config import BOT_TOKEN, OWNER_ID
from database import *

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# =========================
# START
# =========================

@dp.message(Command("start"))
async def start(message: Message):

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏏 TEAM MODE",
                    callback_data="team_mode"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚡ SOLO MODE",
                    callback_data="solo_mode"
                )
            ]
        ]
    )

    await message.answer(
        (
            "🔥 <b>INFERNO CRICKET</b>\n\n"
            "The most cinematic hand cricket bot."
        ),
        reply_markup=kb
    )

# =========================
# TEAM MODE
# =========================

@dp.callback_query(F.data == "team_mode")
async def team_mode(call: CallbackQuery):

    match_data[call.message.chat.id] = {
        "host": call.from_user.id,
        "teamA": [],
        "teamB": [],
        "captainA": None,
        "captainB": None,
        "overs": settings_db["default_overs"],
        "innings": 1,
        "runs": 0,
        "wickets": 0,
        "balls": 0,
        "target": 0,
        "bowler_pick": None,
        "current_batter": None,
        "current_bowler": None
    }

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔵 JOIN TEAM A",
                    callback_data="joinA"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔴 JOIN TEAM B",
                    callback_data="joinB"
                )
            ]
        ]
    )

    await call.message.answer(
        (
            f"👑 HOST: {call.from_user.full_name}\n\n"
            "Players can now join teams."
        ),
        reply_markup=kb
    )

# =========================
# JOIN TEAM A
# =========================

@dp.callback_query(F.data == "joinA")
async def join_a(call: CallbackQuery):

    data = match_data[call.message.chat.id]

    if len(data["teamA"]) >= settings_db["max_players"]:
        return await call.answer("❌ Team A Full", show_alert=True)

    if call.from_user.id not in data["teamA"]:
        data["teamA"].append(call.from_user.id)

    await call.answer("🔥 Joined Team A")

# =========================
# JOIN TEAM B
# =========================

@dp.callback_query(F.data == "joinB")
async def join_b(call: CallbackQuery):

    data = match_data[call.message.chat.id]

    if len(data["teamB"]) >= settings_db["max_players"]:
        return await call.answer("❌ Team B Full", show_alert=True)

    if call.from_user.id not in data["teamB"]:
        data["teamB"].append(call.from_user.id)

    await call.answer("🔥 Joined Team B")

# =========================
# SET OVERS
# =========================

@dp.message(Command("setovers"))
async def set_overs(message: Message):

    args = message.text.split()

    if len(args) < 2:
        return

    if message.chat.id not in match_data:
        return

    data = match_data[message.chat.id]

    if message.from_user.id != data["host"]:
        return

    data["overs"] = int(args[1])

    await message.reply(
        f"🔥 Overs set to {args[1]}"
    )

# =========================
# COMMENTARY
# =========================

COMMENTARY = {
    "0": [
        "🧱 Dead ball.",
        "😴 Nobody moved."
    ],
    "1": [
        "🥱 Just a single.",
        "⚡ Quick run."
    ],
    "2": [
        "🏃 Smart running.",
        "⚡ Sharp cricket."
    ],
    "3": [
        "💀 Fielders confused.",
        "🏃 Chaos in the field."
    ],
    "4": [
        "💥 DISRESPECTFUL.",
        "🔥 Boundary destroyed."
    ],
    "5": [
        "☠️ Misfield disaster.",
        "😈 Fielders sleeping."
    ],
    "6": [
        "🚀 SENT TO ORBIT.",
        "🔥 Bowler traumatized."
    ],
    "out": [
        "💀 PACK YOUR BAGS.",
        "☠️ Absolute humiliation."
    ]
}

# =========================
# BOWLER DM
# =========================

@dp.message(F.chat.type == "private")
async def bowler_dm(message: Message):

    if message.text not in ["1", "2", "3", "4", "5", "6"]:
        return

    for chat_id, data in match_data.items():

        if data["current_bowler"] == message.from_user.id:

            data["bowler_pick"] = int(message.text)

            await bot.send_message(
                OWNER_ID,
                (
                    "📡 <b>LIVE TRACK</b>\n\n"
                    f"🎳 Bowler: {message.from_user.full_name}\n"
                    f"⚡ Selected: {message.text}\n\n"
                    "⏳ Waiting for batter..."
                )
            )

            await message.reply(
                "🔥 Delivery Locked"
            )

# =========================
# GAMEPLAY
# =========================

@dp.message(F.chat.type.in_(["group", "supergroup"]))
async def gameplay(message: Message):

    if message.chat.id not in match_data:
        return

    data = match_data[message.chat.id]

    if data["current_batter"] is None:
        return

    if message.from_user.id != data["current_batter"]:
        return

    if message.text not in [
        "0", "1", "2", "3", "4", "5", "6"
    ]:
        return

    if data["bowler_pick"] is None:
        return await message.reply(
            "⏳ Waiting for bowler."
        )

    batter = int(message.text)
    bowler = data["bowler_pick"]

    if batter == 0:

        result = "0"

    elif batter == bowler:

        result = "out"
        data["wickets"] += 1

    else:

        result = str(batter)
        data["runs"] += batter

    data["balls"] += 1

    commentary = random.choice(
        COMMENTARY[result]
    )

    await message.reply(
        (
            f"{commentary}\n\n"
            f"👤 Batter: {batter}\n"
            f"🎯 Bowler: {bowler}\n\n"
            f"🏏 Score: "
            f"{data['runs']}/{data['wickets']}"
        )
    )

    data["bowler_pick"] = None
# =========================================================
# 👑 FULL OWNER PANEL SYSTEM
# =========================================================

@dp.message(Command("wowadminwow"))
async def owner_panel(message: Message):

    if message.from_user.id != OWNER_ID:
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🎨 Media Control",
                    callback_data="media_panel"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📝 Commentary Control",
                    callback_data="commentary_panel"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⚙️ Match Settings",
                    callback_data="match_panel"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📡 Live Tracker",
                    callback_data="tracker_panel"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🏏 Match Management",
                    callback_data="management_panel"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👥 User Management",
                    callback_data="user_panel"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎭 Celebration Control",
                    callback_data="celebration_panel"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📊 Match Stats",
                    callback_data="stats_panel"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📢 Broadcast",
                    callback_data="broadcast_panel"
                )
            ]
        ]
    )

    await message.answer(
        "👑 INFERNO OWNER PANEL",
        reply_markup=kb
    )


# =========================================================
# 🎨 MEDIA CONTROL
# =========================================================

@dp.callback_query(F.data == "media_panel")
async def media_panel(call: CallbackQuery):

    kb = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🏆 Toss GIF",
                    callback_data="set_toss"
                ),

                InlineKeyboardButton(
                    text="🔥 Six Video",
                    callback_data="set_six"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💀 Out GIF",
                    callback_data="set_out"
                ),

                InlineKeyboardButton(
                    text="🎉 Win Photo",
                    callback_data="set_win"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💯 100 Celebration",
                    callback_data="set_100"
                ),

                InlineKeyboardButton(
                    text="5️⃣0️⃣ 50 Celebration",
                    callback_data="set_50"
                )
            ]
        ]
    )

    await call.message.answer(
        "🎨 MEDIA CONTROL PANEL",
        reply_markup=kb
    )


# =========================================================
# 📝 COMMENTARY PANEL
# =========================================================

@dp.callback_query(F.data == "commentary_panel")
async def commentary_panel(call: CallbackQuery):

    kb = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🔥 Savage Mode",
                    callback_data="savage_mode"
                )
            ],

            [
                InlineKeyboardButton(
                    text="😂 Sarcastic Mode",
                    callback_data="sarcasm_mode"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎭 Cinematic Mode",
                    callback_data="cinematic_mode"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🤖 AI Commentary",
                    callback_data="ai_mode"
                )
            ]
        ]
    )

    await call.message.answer(
        "📝 COMMENTARY CONTROL",
        reply_markup=kb
    )


# =========================================================
# ⚙️ MATCH SETTINGS
# =========================================================

@dp.callback_query(F.data == "match_panel")
async def match_panel(call: CallbackQuery):

    kb = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="⏱ Set Overs",
                    callback_data="set_overs"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👥 Max Players",
                    callback_data="max_players"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔥 Auto Innings",
                    callback_data="auto_innings"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📩 DM Bowling",
                    callback_data="dm_bowling"
                )
            ]
        ]
    )

    await call.message.answer(
        "⚙️ MATCH SETTINGS",
        reply_markup=kb
    )


# =========================================================
# 📡 LIVE TRACKER
# =========================================================

@dp.callback_query(F.data == "tracker_panel")
async def tracker_panel(call: CallbackQuery):

    kb = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🎯 Batter Pick",
                    callback_data="batter_pick"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎳 Bowler Pick",
                    callback_data="bowler_pick"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📜 Match Logs",
                    callback_data="match_logs"
                )
            ]
        ]
    )

    await call.message.answer(
        "📡 LIVE TRACKER PANEL",
        reply_markup=kb
    )


# =========================================================
# 🏏 MATCH MANAGEMENT
# =========================================================

@dp.callback_query(F.data == "management_panel")
async def management_panel(call: CallbackQuery):

    kb = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="▶️ Force Start",
                    callback_data="force_start"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔁 Next Innings",
                    callback_data="next_innings"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🛑 End Match",
                    callback_data="end_match"
                )
            ],

            [
                InlineKeyboardButton(
                    text="✏️ Edit Score",
                    callback_data="edit_score"
                )
            ]
        ]
    )

    await call.message.answer(
        "🏏 MATCH MANAGEMENT",
        reply_markup=kb
    )


# =========================================================
# 👥 USER MANAGEMENT
# =========================================================

@dp.callback_query(F.data == "user_panel")
async def user_panel(call: CallbackQuery):

    kb = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🚫 Ban User",
                    callback_data="ban_user"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Kick Player",
                    callback_data="kick_player"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👑 Make Captain",
                    callback_data="make_captain"
                )
            ],

            [
                InlineKeyboardButton(
                    text="➕ Force Join",
                    callback_data="force_join"
                )
            ]
        ]
    )

    await call.message.answer(
        "👥 USER MANAGEMENT",
        reply_markup=kb
    )


# =========================================================
# 🎭 CELEBRATION PANEL
# =========================================================

@dp.callback_query(F.data == "celebration_panel")
async def celebration_panel(call: CallbackQuery):

    kb = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🔥 Enable 50 Celebration",
                    callback_data="enable_50"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💯 Enable 100 Celebration",
                    callback_data="enable_100"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🏆 Winning Celebration",
                    callback_data="enable_win"
                )
            ]
        ]
    )

    await call.message.answer(
        "🎭 CELEBRATION CONTROL",
        reply_markup=kb
    )


# =========================================================
# 📊 STATS PANEL
# =========================================================

@dp.callback_query(F.data == "stats_panel")
async def stats_panel(call: CallbackQuery):

    await call.message.answer(
        "📊 MATCH STATS PANEL\n\n"
        "• Top Scorer\n"
        "• Most Sixes\n"
        "• Strike Rate\n"
        "• Economy\n"
        "• Match MVP"
    )


# =========================================================
# 📢 BROADCAST PANEL
# =========================================================

@dp.callback_query(F.data == "broadcast_panel")
async def broadcast_panel(call: CallbackQuery):

    await call.message.answer(
        "📢 Send broadcast text now."
                  )
# =========================
# MAIN
# =========================

async def main():

    print("🔥 INFERNO CRICKET STARTED")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
