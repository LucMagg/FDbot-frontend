import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List, Optional

from utils.session_decorator import session_command
from sessions.addcomment import AddCommentSession


class Addcomment(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.choices = None

  async def hero_or_pet_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    langcode = self.bot.language.set_language(interaction=interaction)
    return await self.bot.command.return_autocompletion(self.choices[langcode], current.strip())

  @app_commands.autocomplete(hero_or_pet=hero_or_pet_autocomplete)
  @app_commands.command(name='addcomment')
  @session_command(command_name='addcomment')
  async def addcomment_app_command(self, interaction: discord.Interaction, hero_or_pet: str, comment: Optional[str] = None):
    self.logger.log_only('debug', f'[ADDCOMMENT] hero_or_pet : {hero_or_pet} | comment : {comment}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'hero_or_pet': hero_or_pet,
      'comment': comment
    }
    session = AddCommentSession(session_data)
    await session.start()
  
  async def setup(self, param_list: Optional[list[Dict]] = None):
    if param_list:
      self.choices = param_list
    else:
      self.choices = await self.bot.command.set_choices(['heroes', 'pets'])
  
async def setup(bot):
  await bot.add_cog(Addcomment(bot))