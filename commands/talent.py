import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from utils.session_decorator import session_command
from sessions.talent import TalentSession


class Talent(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.choices = None

  async def talent_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    langcode = self.bot.language.set_language(interaction=interaction)
    return await self.bot.command.return_autocompletion(self.choices[langcode], current.strip())

  @app_commands.autocomplete(talent=talent_autocomplete)
  @app_commands.command(name='talent')
  @session_command(command_name='talent')
  async def talent_app_command(self, interaction: discord.Interaction, talent: str):
    self.logger.log('debug', f'[TALENT] Talent : {talent}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'talent': talent
    }
    session = TalentSession(session_data)
    await session.start()
  
  async def setup(self, param_list: Optional[list[dict]] = None):
    if param_list:
      self.choices = param_list
    else:
      self.choices = await self.bot.command.set_choices(['talents'])

async def setup(bot):
  await bot.add_cog(Talent(bot))