import asyncio
import sqlite3
from datetime import datetime
import pandas as pd

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

TOKEN = "8675118804:AAFrV0th6Y2z-JHw02C1GNO27dbfx_cKQnQ"
ADMIN_ID = 232481679

bot = Bot(token=TOKEN)
dp = Dispatcher()

conn = sqlite3.connect("telegram.db")
cursor = conn.cursor()

# ================= DB =================
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
user_id INTEGER PRIMARY KEY,
username TEXT,
first_name TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS group_preds (
user_id INTEGER,
group_id TEXT,
position INTEGER,
team TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS knockout_preds (
user_id INTEGER,
team TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS champion_pred (
user_id INTEGER PRIMARY KEY,
team TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS scores (
user_id INTEGER PRIMARY KEY,
score INTEGER DEFAULT 0
)""")

conn.commit()

#=================== Exel =================
# ================= EXCEL FILE =================

GROUP_RESULTS = pd.read_excel(
    "worldcup_predictions.xlsx",
    sheet_name="GROUP_STAGE"
)

KNOCKOUT_RESULTS = pd.read_excel(
    "worldcup_predictions.xlsx",
    sheet_name="KNOCKOUT"
)

CHAMPION_RESULT = pd.read_excel(
    "worldcup_predictions.xlsx",
    sheet_name="CHAMPION"
)

# ================= GROUPS =================
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
"J": ["Algeria", "Argentina", "Austria", "Jordan"],
"K": ["Colombia", "DR Congo", "Portugal", "Uzbekistan"],
"L": ["Croatia", "England", "Ghana", "Panama"],
}

GROUP_ORDER = list(GROUPS.keys())
user_state = {}

# ================= START TEXT =================
START_TEXT = """
🤖 گروه هوش مصنوعی CAST تقدیم می‌کند:

⚽  پیش‌بینی جام جهانی2026
پیشبینی در 3 مرحله زیر انجام می‌گیرد.

بعد از انتخاب جایگاه تیم‌ها در هر گروه درست بودن آن را تایید کنید.

1️⃣ تعیین جایگاه گروه‌ها
2️⃣ انتخاب 8 تیم صعودکننده
3️⃣ انتخاب قهرمان

گروه A:
"""

# ================= دائمی دکمه =================
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 داشبورد من")]
        ],
        resize_keyboard=True
    )

# ================= INLINE =================
def group_kb(g):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t, callback_data=f"g_{g}_{t}")]
        for t in GROUPS[g]
    ])

def confirm_group_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ ریست", callback_data="reset_group")],
        [InlineKeyboardButton(text="✅ تایید", callback_data="confirm_group")]
    ])

def knockout_kb(teams):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t, callback_data=f"k_{t}")]
        for t in teams
    ])

def champion_kb(teams):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t, callback_data=f"c_{t}")]
        for t in teams
    ])

# ================= USER =================
def save_user(user):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)",
                   (user.id, user.username, user.first_name))
    cursor.execute("INSERT OR IGNORE INTO scores VALUES (?, 0)", (user.id,))
    conn.commit()


# ================= SCORE =================
def update_scores():

    # ================= READ EXCEL =================
    GROUP_RESULTS = pd.read_excel(
        "worldcup_predictions.xlsx",
        sheet_name="GROUP_STAGE"
    )

    KNOCKOUT_RESULTS = pd.read_excel(
        "worldcup_predictions.xlsx",
        sheet_name="KNOCKOUT"
    )

    CHAMPION_RESULT = pd.read_excel(
        "worldcup_predictions.xlsx",
        sheet_name="CHAMPION"
    )
    print("EXCEL UPDATED")
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    for (uid,) in users:

        total = 0

        # ================= GROUP STAGE =================
       # ================= GROUP STAGE =================
        cursor.execute("""
        SELECT group_id, position, team
        FROM group_preds
        WHERE user_id = ?
        """, (uid,))

        preds = cursor.fetchall()

        # تیم‌های سومی که واقعاً صعود کرده‌اند
        real_best_thirds = set(KNOCKOUT_RESULTS["team"].tolist())

        # تیم‌های سومی که کاربر به عنوان صعودکننده انتخاب کرده
        cursor.execute("""
        SELECT team
        FROM knockout_preds
        WHERE user_id = ?
        """, (uid,))
        user_best_thirds = set(row[0] for row in cursor.fetchall())

        for group_id, position, team in preds:

            real_row = GROUP_RESULTS[
               (GROUP_RESULTS["group"] == group_id) &
               (GROUP_RESULTS["team"] == team)
            ]

            if real_row.empty:
                continue

            real_pos = int(real_row.iloc[0]["position"])

            # آیا واقعاً صعود کرده؟
            real_qualified = (
                real_pos in [1, 2]
                or team in real_best_thirds
            )

            # آیا کاربر صعودش را پیش‌بینی کرده؟
            predicted_qualified = (
                position in [1, 2]
                or team in user_best_thirds
            )

            # جایگاه دقیق
            if real_pos == position:
                total += 5

            # فقط صعود درست بوده
            elif real_qualified and predicted_qualified:
                total += 3
        # ================= KNOCKOUT =================
        cursor.execute("""
        SELECT team FROM knockout_preds
        WHERE user_id = ?
        """, (uid,))

        knock_preds = cursor.fetchall()

        for (team,) in knock_preds:

            match = KNOCKOUT_RESULTS[
                KNOCKOUT_RESULTS["team"] == team
            ]

            if not match.empty:
                total += 5

        # ================= CHAMPION =================
        cursor.execute("""
        SELECT team FROM champion_pred
        WHERE user_id = ?
        """, (uid,))

        champ = cursor.fetchone()

        if champ:

            match = CHAMPION_RESULT[
                CHAMPION_RESULT["team"] == champ[0]
            ]

            if not match.empty:
                total += 10

        # ================= SAVE SCORE =================
        cursor.execute("""
        UPDATE scores
        SET score = ?
        WHERE user_id = ?
        """, (total, uid))

    conn.commit()

# ================= DASHBOARD =================
async def dashboard(user_id: int, message):

    score = cursor.execute("SELECT score FROM scores WHERE user_id=?", (user_id,)).fetchone()

    rank = cursor.execute("""
    SELECT COUNT(*) + 1
    FROM scores
    WHERE score > (SELECT score FROM scores WHERE user_id=?)
    """, (user_id,)).fetchone()[0]

    groups = cursor.execute("""
    SELECT group_id, position, team
    FROM group_preds
    WHERE user_id=?
    ORDER BY group_id, position
    """, (user_id,)).fetchall()

    knock = cursor.execute("""
    SELECT team FROM knockout_preds WHERE user_id=?
    """, (user_id,)).fetchall()

    champ = cursor.execute("""
    SELECT team FROM champion_pred WHERE user_id=?
    """, (user_id,)).fetchone()

    text = "📊 داشبورد شما\n\n"
    text += f"🏆 امتیاز: {score[0] if score else 0}\n"
    text += f"📊 رتبه: {rank}\n\n"

    current = ""

    for g, p, t in groups:
        if current != g:
            current = g
            text += f"\n🏆 گروه {g}\n"

        text += f"{t}\n"

    text += "\n🚀 صعودی‌ها:\n"
    for k in knock:
        text += f"✅ {k[0]}\n"

    if champ:
        text += f"\n👑 قهرمان: {champ[0]}"

    await message.answer(text)

# ================= START =================
@dp.message(Command("start"))
async def start(m: types.Message):

    save_user(m.from_user)

    user_state[m.from_user.id] = {
        "group_index": 0,
        "picked": [],
        "knockout": [],
        "champion": None
    }

    await m.answer(
        START_TEXT,
        reply_markup=main_menu()
    )

    await m.answer(
        "گروه A",
        reply_markup=group_kb("A")
    )

# ================= DASHBOARD BUTTON =================
@dp.message(lambda m: m.text == "📊 داشبورد من")
async def dash(m: types.Message):
    await dashboard(m.from_user.id, m)


# ================= CALLBACK =================
@dp.callback_query()
async def cb(c: types.CallbackQuery):

    uid = c.from_user.id
    state = user_state.get(uid)
    data = c.data

    if not state:
        await c.answer("اول /start بزن")
        return

    # ================= GROUP PICKS =================
    if data.startswith("g_"):

        _, g, t = data.split("_")

        # جلوگیری از انتخاب تکراری
        if t in state["picked"]:
            await c.answer("این تیم قبلا انتخاب شده")
            return

        state["picked"].append(t)

        await c.message.answer(
            f"""
✅ {t} انتخاب شد

{len(state['picked'])}/4
"""
        )

        # وقتی 4 تیم انتخاب شد
        if len(state["picked"]) == 4:

            await c.message.answer(
                f"""
🏁 انتخاب‌های شما برای گروه {g}

🥇 {state['picked'][0]}
🥈 {state['picked'][1]}
🥉 {state['picked'][2]}
4️⃣ {state['picked'][3]}

آیا تایید می‌کنی؟
""",
                reply_markup=confirm_group_kb()
            )

    # ================= RESET GROUP =================
    elif data == "reset_group":

        state["picked"] = []

        current_group = GROUP_ORDER[state["group_index"]]

        await c.message.answer(
            f"""
🔄 گروه {current_group} ریست شد

دوباره انتخاب کن
""",
            reply_markup=group_kb(current_group)
        )

    # ================= CONFIRM GROUP =================
    elif data == "confirm_group":

        g = GROUP_ORDER[state["group_index"]]

        cursor.execute("""
        DELETE FROM group_preds
        WHERE user_id=?
        AND group_id=?
        """, (uid, g))

        for i, t in enumerate(state["picked"], 1):

            cursor.execute("""
            INSERT INTO group_preds
            VALUES (?, ?, ?, ?)
            """, (uid, g, i, t))

        conn.commit()

        state["group_index"] += 1
        state["picked"] = []

        # ================= NEXT GROUP =================
        if state["group_index"] < len(GROUP_ORDER):

            nxt = GROUP_ORDER[state["group_index"]]

            await c.message.answer(
                f"""
🏆 حالا گروه {nxt} رو پیش‌بینی کن

تیم‌ها رو به ترتیب انتخاب کن:
"""
            )

            await c.message.answer(
                f"گروه {nxt}",
                reply_markup=group_kb(nxt)
            )

        # ================= THIRD TEAMS =================
        else:

            third = [t[0] for t in cursor.execute("""
            SELECT team
            FROM group_preds
            WHERE position=3
            AND user_id=?
            """, (uid,))]

            await c.message.answer(
                """
🎉 مرحله گروهی تمام شد

حالا از بین تیم‌های سوم
8 تیم صعودکننده را انتخاب کن
"""
            )

            await c.message.answer(
                "👇",
                reply_markup=knockout_kb(third)
            )

    # ================= KNOCKOUT =================
    elif data.startswith("k_"):

        t = data[2:]

        if t in state["knockout"]:
            await c.answer("قبلا انتخاب شده")
            return

        if len(state["knockout"]) >= 8:
            await c.answer("8 تیم انتخاب شده")
            return

        state["knockout"].append(t)

        await c.message.answer(
            f"""
✅ {t}

{len(state['knockout'])}/8
"""
        )

        # وقتی 8 تیم کامل شد
        if len(state["knockout"]) == 8:

            cursor.execute("""
            DELETE FROM knockout_preds
            WHERE user_id=?
            """, (uid,))

            for team in state["knockout"]:

                cursor.execute("""
                INSERT INTO knockout_preds
                VALUES (?, ?)
                """, (uid, team))

            conn.commit()

            # همه تیم‌های صعودکننده
            qualified_teams = []

            cursor.execute("""
            SELECT team
            FROM group_preds
            WHERE user_id = ?
            AND (position = 1 OR position = 2)
            """, (uid,))

            top_teams = cursor.fetchall()

            for team_row in top_teams:
                qualified_teams.append(team_row[0])

            for team in state["knockout"]:
                qualified_teams.append(team)

            await c.message.answer(
                """
🏆 حالا قهرمان جام جهانی رو انتخاب کن
""",
                reply_markup=champion_kb(qualified_teams)
            )

    # ================= CHAMPION =================
    elif data.startswith("c_"):

        t = data[2:]

        state["champion"] = t

        cursor.execute("""
        INSERT OR REPLACE INTO champion_pred
        VALUES (?, ?)
        """, (uid, t))

        conn.commit()

        update_scores()

        # ================= SUMMARY =================
        summary = "🔥 پیش‌بینی کامل شد\n\n"

        cursor.execute("""
        SELECT group_id, position, team
        FROM group_preds
        WHERE user_id = ?
        ORDER BY group_id, position
        """, (uid,))

        rows = cursor.fetchall()

        current_group = ""

        for group_id, position, team in rows:

            if current_group != group_id:
                current_group = group_id
                summary += f"\n🏆 گروه {group_id}\n"

            if position == 1:
                summary += f"🥇 {team}\n"

            elif position == 2:
                summary += f"🥈 {team}\n"

            elif position == 3:

                if team in state["knockout"]:
                    summary += f"⭐ {team} (صعود)\n"
                else:
                    summary += f"🥉 {team}\n"

            elif position == 4:
                summary += f"4️⃣ {team}\n"

        summary += "\n👑 قهرمان:\n"
        summary += f"{t}"

        # رتبه
        cursor.execute("""
        SELECT COUNT(*) + 1
        FROM scores
        WHERE score > (
            SELECT score
            FROM scores
            WHERE user_id = ?
        )
        """, (uid,))

        rank = cursor.fetchone()[0]

        cursor.execute("""
        SELECT score
        FROM scores
        WHERE user_id = ?
        """, (uid,))

        score = cursor.fetchone()

        summary += f"\n\n🏆 امتیاز: {score[0]}"
        summary += f"\n📊 رتبه: {rank}"

        summary += "\n\n📌 دستورات مهم:"
        summary += "\n/refresh → اعمال نتایج جدید مسابقات و امتیاز جدید"
        

        await c.message.answer(summary)

    await c.answer()


#==================admin=================
@dp.message(Command("admin"))
async def admin(m: types.Message):

    if m.from_user.id != ADMIN_ID:
        return await m.answer("⛔ دسترسی نداری")

    # همه کاربران + امتیاز
    rows = cursor.execute("""
    SELECT users.first_name, users.username, scores.score
    FROM users
    JOIN scores ON users.user_id = scores.user_id
    ORDER BY scores.score DESC
    """).fetchall()

    if not rows:
        return await m.answer("هیچ کاربری ثبت نشده")

    total_users = len(rows)
    max_score = max([r[2] for r in rows]) if rows else 0
    avg_score = sum([r[2] for r in rows]) / total_users

    text = "🛠 پنل مدیریت مسابقه\n\n"

    text += f"👥 شرکت‌کننده‌ها: {total_users}\n"
    text += f"🏆 بیشترین امتیاز: {max_score}\n"
    text += f"📊 میانگین امتیاز: {avg_score:.1f}\n\n"

    text += "📋 لیست کامل:\n\n"

    for i, (name, username, score) in enumerate(rows, 1):

        uname = f"@{username}" if username else "—"

        # رتبه همون ترتیب لیست
        text += f"{i}. {name} ({uname}) — {score} امتیاز\n"

    await m.answer(text)    
   

# ================= REFRESH SCORES =================
@dp.message(Command("refresh"))
async def refresh_scores(m: types.Message):

    if m.from_user.id != ADMIN_ID:
        return await m.answer("⛔ دسترسی نداری")

    update_scores()

    await m.answer("✅ امتیازها از اکسل دوباره محاسبه شد")    

# ================= RUN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

