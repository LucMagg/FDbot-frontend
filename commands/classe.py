import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from utils.session_decorator import session_command
from sessions.classe import ClasseSession


class Classe(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.choices = None

  async def classe_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    langcode = self.bot.language.set_language(interaction=interaction)
    return await self.bot.command.return_autocompletion(self.choices[langcode], current.strip())

  @app_commands.autocomplete(classe=classe_autocomplete)
  @app_commands.command(name='class')
  @session_command(command_name='class')
  async def classe_app_command(self, interaction: discord.Interaction, classe: str):
    self.logger.log_only('debug', f'[CLASS] Classe : {classe}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'classe': classe
    }
    session = ClasseSession(session_data)
    await session.start()
  
  async def setup(self, param_list: Optional[list[dict]] = None):
    if param_list:
      self.choices = param_list
    else:
      self.choices = await self.bot.command.set_choices(['classes'])

async def setup(bot):
  await bot.add_cog(Classe(bot))