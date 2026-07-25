import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from utils.session_decorator import session_command
from sessions.setbotlanguage import SetbotlanguageSession


class Setbotlanguage(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.choices = None

  async def language_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    langcode = self.bot.language.set_language(interaction=interaction)
    return await self.bot.command.return_autocompletion(self.choices[langcode], current.strip())

  @app_commands.default_permissions(administrator=True)
  @app_commands.autocomplete(language=language_autocomplete)
  @app_commands.command(name='setbotlanguage')
  @session_command(command_name='setbotlanguage')
  async def setbotlanguage_app_command(self, interaction: discord.Interaction, language: str):
    self.logger.log_only('debug', f'[SETBOTLANGUAGE] Language : {language}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'language': language
    }
    session = SetbotlanguageSession(session_data)
    await session.start()
    
  async def setup(self, param_list: Optional[list[dict]] = None):
    if param_list:
      self.choices = param_list
    else:
      self.choices = await self.bot.command.set_choices(['languages'])
  
async def setup(bot):
  await bot.add_cog(Setbotlanguage(bot))