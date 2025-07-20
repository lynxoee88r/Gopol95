from telegram.ext import ApplicationBuilder, CommandHandler
from checker import start, stop, mass, txt, st, admin, listadmins, deladmin
from config import BOT_TOKEN

import asyncio
import nest_asyncio
nest_asyncio.apply()

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(True).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mass", mass))
    app.add_handler(CommandHandler("txt", txt))
    app.add_handler(CommandHandler("st", st))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("listadmins", listadmins))
    app.add_handler(CommandHandler("deladmin", deladmin))

    print("✅ Bot Running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
