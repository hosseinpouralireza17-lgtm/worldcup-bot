
import asyncio
import sqlite3
from datetime import datetime

import pandas as pd

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# =========================
# TOKEN
# =========================
TOKEN = "8675118804:AAFrV0th6Y2z-JHw02C1GNO27dbfx_cKQnQ"

# =========================
# DEADLINE
# =========================
DEADLINE = datetime(2026, 6, 1, 18, 0)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("telegram.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS group_preds (
    user_id INTEGER,
    group_id TEXT,
    position INTEGER,
    team TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS knockout_preds (
    user_id INTEGER,
    team TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS champion_pred (
    user_id INTEGER PRIMARY KEY,
    team TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS scores (
    user_id INTEGER PRIMARY KEY,
    score INTEGER DEFAULT 0
)
""")

conn.commit()

# =========================
# EXCEL
# =========================
GROUP_RESULTS = pd.read_excel(
    "worldcup_predictions.xlsx",
    sheet_name="GROUP_STAGE"
)

# =========================
# GROUPS
# =========================
GROUPS = {
"A": ["Czechia", "Mexico", "South Africa", "South Korea"],
"B": ["Bosnia and Herzegovina", "Canada", "Qatar", "Switzerland"],
"C": ["Brazil", "Haiti", "Morocco", "Scotland"],
"D": ["Australia", "Paraguay", "Turkey", "Usa"],
"E": ["Curacao", "Ecuador", "Germany", "Ivory Coast"],
"F": ["Japan", "Netherlands", "Sweden", "Tunisia"],
"G": ["Belgium", "Egypt", "Iran", "New Zealand"],
"H": ["Cape Verde", "Saudi Arabia", "Spain", "Uruguay"],
"I": ["France", "Iraq", "Norway", "Senegal"],
"J": ["Algeria", "Argentina", "Austia", "Jordan"],
"K": ["Colombia", "DR Congo", "Portugal", "Uzbekistan"],
"L": ["Croatia", "England", "Ghana", "Panama"],
}

GROUP_ORDER = list(GROUPS.keys())

user_state = {}

# =========================
# START TEXT
# =========================
START_TEXT = """
⚽ سلام به ربات پیش‌بینی جام جهانی خوش اومدی

📌 مراحل مسابقه:

1️⃣ مرحله اول:
به ترتیب جایگاه تیم‌ها در هر گروه رو مشخص کن

2️⃣ مرحله دوم:
از بین تیم‌های سوم هر گروه (12 تیم)،
فقط 8 تیمی که فکر می‌کنی صعود می‌کنن رو انتخاب کن

3️⃣ مرحله نهایی:
قهرمان تورنمنت رو انتخاب کن

🏆 به 3 نفر اول جایزه داده میشه
"""

# =========================
# KEYBOARDS
# =========================
def start_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🚀 شروع کنیم",
                callback_data="start_game"
            )]
        ]
    )

def group_kb(group):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=t,
                callback_data=f"g_{group}_{t}"
            )]
            for t in GROUPS[group]
        ]
    )

def confirm_group_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🔁 ریست گروه",
                callback_data="reset_group"
            )],
            [InlineKeyboardButton(
                text="✅ تایید گروه",
                callback_data="confirm_group"
            )]
        ]
    )

def knockout_kb(third_teams):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=t,
                callback_data=f"k_{t}"
            )]
            for t in third_teams
        ]
    )

def champion_kb(teams):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=t,
                callback_data=f"c_{t}"
            )]
            for t in teams
        ]
    )

# =========================
# SAVE USER
# =========================
def save_user(user):

    cursor.execute("""
    INSERT OR IGNORE INTO users VALUES (?, ?, ?)
    """, (
        user.id,
        user.username,
        user.first_name
    ))

    cursor.execute("""
    INSERT OR IGNORE INTO scores VALUES (?, 0)
    """, (user.id,))

    conn.commit()

# =========================
# UPDATE SCORES
# =========================
def update_scores():

    cursor.execute("""
    SELECT user_id FROM users
    """)

    users = cursor.fetchall()

    for (user_id,) in users:

        total = 0

        cursor.execute("""
        SELECT group_id, position, team
        FROM group_preds
        WHERE user_id = ?
        """, (user_id,))

        preds = cursor.fetchall()

        for group_id, position, team in preds:

            match = GROUP_RESULTS[
                (GROUP_RESULTS["group"] == group_id) &
                (GROUP_RESULTS["team"] == team) &
                (GROUP_RESULTS["position"] == position)
            ]

            if not match.empty:
                total += 5

        cursor.execute("""
        UPDATE scores
        SET score = ?
        WHERE user_id = ?
        """, (total, user_id))

    conn.commit()

# =========================
# START
# =========================
@dp.message(Command("start"))
async def start(message: types.Message):

    if datetime.now() > DEADLINE:
        await message.answer(
            "⛔ زمان پیش‌بینی تموم شده"
        )
        return

    save_user(message.from_user)

    await message.answer(
        START_TEXT,
        reply_markup=start_kb()
    )

# =========================
# CALLBACKS
# =========================
@dp.callback_query()
async def cb(callback: types.CallbackQuery):

    user_id = callback.from_user.id

    # =========================
    # START GAME
    # =========================
    if callback.data == "start_game":

        user_state[user_id] = {
            "group_index": 0,
            "picked": [],
            "knockout": [],
            "champion": None
        }

        first_group = GROUP_ORDER[0]

        await callback.message.answer(
            f"""
🏆 داری گروه {first_group} رو پیش‌بینی می‌کنی

📌 تیم‌ها رو به ترتیب انتخاب کن:

🥇 تیم اول
🥈 تیم دوم
🥉 تیم سوم
4️⃣ تیم چهارم

⚠ اگر اشتباه کردی
گروه رو ریست کن
""",
            reply_markup=group_kb(first_group)
        )

        await callback.answer()
        return

    state = user_state.get(user_id)

    if not state:
        await callback.answer("اول /start بزن")
        return

    # =========================
    # GROUP PICKS
    # =========================
    if callback.data.startswith("g_"):

        _, group, team = callback.data.split("_")

        if team not in state["picked"]:
            state["picked"].append(team)

        await callback.message.answer(
            f"""
✅ {team} ثبت شد

{len(state['picked'])}/4
"""
        )

        if len(state["picked"]) == 4:

            await callback.message.answer(
                f"""
🏁 انتخاب‌های شما:

🥇 {state['picked'][0]}
🥈 {state['picked'][1]}
🥉 {state['picked'][2]}
4️⃣ {state['picked'][3]}

⚠ اگر اشتباهه ریست کن
""",
                reply_markup=confirm_group_kb()
            )

    # =========================
    # RESET GROUP
    # =========================
    elif callback.data == "reset_group":

        state["picked"] = []

        current_group = GROUP_ORDER[state["group_index"]]

        await callback.message.answer(
            f"""
🔁 گروه {current_group} ریست شد

دوباره انتخاب کن
""",
            reply_markup=group_kb(current_group)
        )

    # =========================
    # CONFIRM GROUP
    # =========================
    elif callback.data == "confirm_group":

        group = GROUP_ORDER[state["group_index"]]

        cursor.execute("""
        DELETE FROM group_preds
        WHERE user_id = ?
        AND group_id = ?
        """, (user_id, group))

        for i, team in enumerate(state["picked"], start=1):

            cursor.execute("""
            INSERT INTO group_preds
            VALUES (?, ?, ?, ?)
            """, (
                user_id,
                group,
                i,
                team
            ))

        conn.commit()

        state["group_index"] += 1
        state["picked"] = []

        # =========================
        # NEXT GROUP
        # =========================
        if state["group_index"] < len(GROUP_ORDER):

            next_group = GROUP_ORDER[state["group_index"]]

            await callback.message.answer(
                f"""
🏆 حالا داری گروه {next_group} رو پیش‌بینی می‌کنی

⚠ اگر اشتباه کردی
گروه رو ریست کن
"""
            )

            await callback.message.answer(
                "👇",
                reply_markup=group_kb(next_group)
            )

            return

        # =========================
        # THIRD TEAMS
        # =========================
        third_teams = cursor.execute("""
        SELECT team
        FROM group_preds
        WHERE position = 3
        AND user_id = ?
        """, (user_id,)).fetchall()

        third_teams = [t[0] for t in third_teams]

        await callback.message.answer(
            """
🎉 مرحله گروهی تمام شد

🏆 حالا از بین 12 تیم سومی
که خودت انتخاب کردی

8 تیمی که فکر میکنی
صعود میکنن رو انتخاب کن
"""
        )

        await callback.message.answer(
            "👇",
            reply_markup=knockout_kb(third_teams)
        )

    # =========================
    # KNOCKOUT
    # =========================
    elif callback.data.startswith("k_"):

        team = callback.data[2:]

        if (
            team not in state["knockout"]
            and len(state["knockout"]) < 8
        ):
            state["knockout"].append(team)

        await callback.message.answer(
            f"""
✅ {team}

{len(state['knockout'])}/8
"""
        )

        if len(state["knockout"]) == 8:

            cursor.execute("""
            DELETE FROM knockout_preds
            WHERE user_id = ?
            """, (user_id,))

            for t in state["knockout"]:

                cursor.execute("""
                INSERT INTO knockout_preds
                VALUES (?, ?)
                """, (
                    user_id,
                    t
                ))

            conn.commit()

            await callback.message.answer(
                """
🏆 حالا قهرمان جام جهانی رو انتخاب کن
""",
                reply_markup=champion_kb(
                    state["knockout"]
                )
            )

    # =========================
    # CHAMPION
    # =========================
    elif callback.data.startswith("c_"):

        team = callback.data[2:]

        state["champion"] = team

        cursor.execute("""
        INSERT OR REPLACE INTO champion_pred
        VALUES (?, ?)
        """, (
            user_id,
            team
        ))

        conn.commit()

        update_scores()

        await callback.message.answer(
            f"""
🔥 پیش‌بینی کامل شد

👑 قهرمان:
{team}

موفق باشی 🔥
"""
        )

    await callback.answer()

# =========================
# PROFILE
# =========================
@dp.message(Command("me"))
async def me(message: types.Message):

    user_id = message.from_user.id

    cursor.execute("""
    SELECT score
    FROM scores
    WHERE user_id = ?
    """, (user_id,))

    score = cursor.fetchone()

    if not score:
        await message.answer(
            "پروفایلی پیدا نشد"
        )
        return

    cursor.execute("""
    SELECT group_id, position, team
    FROM group_preds
    WHERE user_id = ?
    ORDER BY group_id, position
    """, (user_id,))

    rows = cursor.fetchall()

    text = "👤 پروفایل شما\n\n"

    text += f"🏆 امتیاز: {score[0]}\n"

    current_group = ""

    for group_id, position, team in rows:

        if current_group != group_id:

            current_group = group_id

            text += f"\n🏆 گروه {group_id}\n"

        if position == 1:
            text += f"🥇 {team}\n"

        elif position == 2:
            text += f"🥈 {team}\n"

        elif position == 3:
            text += f"⭐ {team} ⭐\n"

        elif position == 4:
            text += f"4️⃣ {team}\n"

    cursor.execute("""
    SELECT team
    FROM knockout_preds
    WHERE user_id = ?
    """, (user_id,))

    knockout = cursor.fetchall()

    text += "\n🚀 تیم‌های صعودکننده:\n"

    for t in knockout:
        text += f"✅ {t[0]}\n"

    cursor.execute("""
    SELECT team
    FROM champion_pred
    WHERE user_id = ?
    """, (user_id,))

    champ = cursor.fetchone()

    if champ:
        text += f"\n👑 قهرمان: {champ[0]}"

    await message.answer(text)

# =========================
# LEADERBOARD
# =========================
@dp.message(Command("leaderboard"))
async def leaderboard(message: types.Message):

    cursor.execute("""
    SELECT users.first_name, scores.score
    FROM scores
    JOIN users
    ON users.user_id = scores.user_id
    ORDER BY scores.score DESC
    LIMIT 10
    """)

    rows = cursor.fetchall()

    if not rows:
        await message.answer(
            "هنوز کسی امتیاز نگرفته"
        )
        return

    text = "🏆 جدول امتیازات\n\n"

    for i, (name, score) in enumerate(rows, start=1):

        medal = "▫️"

        if i == 1:
            medal = "🥇"

        elif i == 2:
            medal = "🥈"

        elif i == 3:
            medal = "🥉"

        text += (
            f"{medal} "
            f"{i}. "
            f"{name} — "
            f"{score} امتیاز\n"
        )

    await message.answer(text)

# =========================
# MAIN
# =========================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
