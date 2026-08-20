import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List, Optional

from utils.session_decorator import session_command
from sessions.exclusive import ExclusiveSession


class Exclusive(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.choices = None

  async def event_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    langcode = self.bot.language.set_language(interaction=interaction)
    return await self.bot.command.return_autocompletion(self.choices[langcode], current.strip())

  @app_commands.autocomplete(event=event_autocomplete)
  @app_commands.command(name='exclusive')
  @session_command(command_name='exclusive')
  async def exclusive_app_command(self, interaction: discord.Interaction, event: str):
    self.logger.log('debug', f'[EXCLUSIVE] Event : {event}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'event': event
    }
    session = ExclusiveSession(session_data)
    await session.start()
    
  async def setup(self, param_list: Optional[list[Dict]] = None):
    if param_list:
      self.choices = param_list
    else:
      self.choices = await self.bot.command.set_choices(['exclusives'])

async def setup(bot):
  await bot.add_cog(Exclusive(bot))