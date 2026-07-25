from datetime import datetime, timezone
from discord.ext import tasks

from services.loop.spire.spire_ranking import SpireRankingSession
from services.loop.spire.spire_reminder import SpireReminderSession
from services.loop.dc_cleaner import DcCleanerSession


class LoopService:
  def __init__(self, bot, loop: str):
    self.bot = bot
    self.loop = loop

  async def start(self):
    match self.loop:
      case 'spire_ranking':
        self.spire_results_session.start()
      case 'spire_reminder':
        self.spire_reminder_session.start()
      case 'dc_cleaner':
        self.dc_cleaner_session.start()

  @tasks.loop(time=datetime.now(tz=timezone.utc).replace(hour=11, minute=0, second=0, microsecond=0).time())
  async def spire_results_session(self):
    session = SpireRankingSession({'bot': self.bot})
    await session.start()

  @tasks.loop(time=datetime.now(tz=timezone.utc).replace(hour=10, minute=0, second=0, microsecond=0).time())
  async def spire_reminder_session(self):
    session = SpireReminderSession({'bot': self.bot})
    await session.start()

  @tasks.loop(time=datetime.now(tz=timezone.utc).replace(hour=11, minute=0, second=0, microsecond=0).time())
  async def dc_cleaner_session(self):
    session = DcCleanerSession({'bot': self.bot})
    await session.start()

  @spire_results_session.before_loop
  async def before_results_loop(self):
    await self.bot.wait_until_ready()

  @spire_reminder_session.before_loop
  async def before_reminder_loop(self):
    await self.bot.wait_until_ready()

  @dc_cleaner_session.before_loop
  async def before_cleaner_loop(self):
    await self.bot.wait_until_ready()