import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from utils.session_decorator import session_command
from sessions.hero import HeroSession


class Hero(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.choices = None

  async def hero_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    langcode = self.bot.language.set_language(interaction=interaction)
    return await self.bot.command.return_autocompletion(self.choices[langcode], current.strip())

  @app_commands.autocomplete(hero=hero_autocomplete)
  @app_commands.command(name='hero')
  @session_command(command_name='hero')
  async def hero_app_command(self, interaction: discord.Interaction, hero: str):
    self.logger.log_only('debug', f'[HERO] Hero : {hero}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'hero': hero
    }
    session = HeroSession(session_data)
    await session.start()
  
  async def setup(self, param_list: Optional[list[dict]] = None):
    if param_list:
      self.choices = param_list
    else:
      self.choices = await self.bot.command.set_choices(['heroes'])

async def setup(bot):
  await bot.add_cog(Hero(bot))