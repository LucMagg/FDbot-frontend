import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from utils.session_decorator import session_command
from sessions.dc_add import DcAddSession
from sessions.dc_show import DcShowSession

from utils.misc_utils import nick

class Dc(commands.Cog):
  dc = app_commands.Group(name='dc', description='...')

  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.missing_levels = None
    self.existing_levels = None

  async def level_add_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    langcode = self.bot.language.set_language(interaction=interaction)
    return await self.bot.command.return_autocompletion(self.missing_levels[langcode], current.strip())
  
  async def level_show_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    langcode = self.bot.language.set_language(interaction=interaction)
    return await self.bot.command.return_autocompletion(self.existing_levels[langcode], current.strip())

  @app_commands.autocomplete(level=level_add_autocomplete)
  @dc.command(name='add')
  @session_command(command_name='dc add')
  async def dcadd_app_command(
    self,
    interaction: discord.Interaction,
    level: str,
    screenshot_1: Optional[discord.Attachment] = None,
    screenshot_2: Optional[discord.Attachment] = None,
    screenshot_3: Optional[discord.Attachment] = None,
    replay: Optional[str] = None
  ):
    self.logger.log_only('debug', (
      f'[DC ADD] Level : {level} | '
      f'Screenshot1 : {screenshot_1.url if screenshot_1 else 'no screenshot'} | '
      f'Screenshot2 : {screenshot_2.url if screenshot_2 else 'no screenshot'} | '
      f'Screenshot3 : {screenshot_3.url if screenshot_3 else 'no screenshot'} | '
      f'Replay : {replay} | User : {nick(interaction)}')
    )
    session_data = {
      'cog': self,
      'interaction': interaction,
      'level': level,
      'screenshots': [screenshot_1, screenshot_2, screenshot_3],
      'replay': replay
    }
    session = DcAddSession(session_data)
    await session.start()

  @app_commands.autocomplete(level=level_show_autocomplete)
  @dc.command(name='show')
  @session_command(command_name='dc show')
  async def dcshow_app_command(self, interaction: discord.Interaction, level: str):
    self.logger.log_only('debug', f'[DC SHOW] Level : {level}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'level': level
    }
    session = DcShowSession(session_data)
    await session.start()

  async def setup(self, missing_levels: Optional[list[str]] = None, existing_levels: Optional[list[str]] = None):
    self.missing_levels, self.existing_levels = await self.bot.command.set_choices(['dc levels'])
    if missing_levels:
      self.missing_levels = missing_levels
    if existing_levels:
      self.existing_levels = existing_levels
    
async def setup(bot):
  await bot.add_cog(Dc(bot))