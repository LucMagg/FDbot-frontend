import asyncio
from bot.bot import MyBot
from config import BOT_KEY
import discord

async def main():
  bot = MyBot()

  try:
    await bot.start(BOT_KEY)
  except KeyboardInterrupt:
    await bot.close()


if __name__ == '__main__':
  asyncio.run(main())