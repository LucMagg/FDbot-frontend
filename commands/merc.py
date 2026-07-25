import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from utils.session_decorator import session_command
from sessions.merc_ask import MercAskSession
from sessions.merc_show import MercShowSession
from sessions.merc_register import MercRegisterSession


class Merc(commands.Cog):
  merc = app_commands.Group(name='merc', description='...')

  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.hero_list = None
    self.hero_choices = None
    self.user_choices = None

  async def hero_list_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    langcode = self.bot.language.set_language(interaction=interaction)
    return await self.bot.command.return_autocompletion(self.hero_list[langcode], current.strip())

  async def hero_choices_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    langcode = self.bot.language.set_language(interaction=interaction)
    guild_id = interaction.guild_id
    return await self.bot.command.return_autocompletion(self.hero_choices[langcode][guild_id], current.strip())
  
  async def user_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    langcode = self.bot.language.set_language(interaction=interaction)
    guild_id = interaction.guild_id
    return await self.bot.command.return_autocompletion(self.user_choices[langcode][guild_id], current.strip())

  @app_commands.autocomplete(hero=hero_choices_autocomplete)
  @merc.command(name='ask')
  @session_command(command_name='merc ask')
  async def mercask_app_command(self, interaction: discord.Interaction, hero: str):
    self.logger.log_only('debug', f'[MERC ASK] Hero : {hero}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'hero': hero
    }
    session = MercAskSession(session_data)
    await session.start()

  @app_commands.autocomplete(user=user_autocomplete)
  @merc.command(name='show')
  @session_command(command_name='merc show')
  async def mercshow_app_command(self, interaction: discord.Interaction, user: str):
    self.logger.log_only('debug', f'[MERC SHOW] User : {user}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'user_id': user
    }
    session = MercShowSession(session_data)
    await session.start()
  
  @app_commands.autocomplete(hero=hero_list_autocomplete)
  @merc.command(name='register')
  @session_command(command_name='merc register')
  async def mercregister_app_command(
      self, 
      interaction: discord.Interaction, 
      hero: str, 
      ascend: Optional[str] = None, 
      pet: Optional[bool] = None, 
      pet_talent: Optional[bool] = None, 
      a2_talent: Optional[bool] = None, 
      a3_talent: Optional[bool] = None, 
      a4_talent: Optional[bool] = None, 
      merge: Optional[str] = None
    ):
    merc = {'name': hero, 'ascend': ascend, 'a2_talent': a2_talent, 'a3_talent': a3_talent, 'a4_talent': a4_talent, 'merge': merge, 'pet': pet, 'pet_talent': pet_talent}
    self.logger.log_only('debug', f'[MERC REGISTER] Merc : {merc}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'merc': merc
    }
    session = MercRegisterSession(session_data)
    await session.start()

  async def setup(self, hero_list: Optional[list[dict]] = None, hero_choices: Optional[list[dict]] = None, user_choices: Optional[list[dict]] = None):
    if hero_list:
      self.hero_list = hero_list
    else:
      self.hero_list = await self.bot.command.set_choices(['heroes'])
    if hero_choices:
      self.hero_choices = hero_choices
    else:
      self.hero_choices = await self.bot.command.set_choices(['merc heroes'])
    if user_choices:
      self.user_choices = user_choices
    else:
      self.user_choices = await self.bot.command.set_choices(['merc users'])
    
async def setup(bot):
  await bot.add_cog(Merc(bot))