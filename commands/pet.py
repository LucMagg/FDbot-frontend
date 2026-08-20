import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from utils.session_decorator import session_command
from sessions.pet import PetSession


class Pet(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.choices = None

  async def pet_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    langcode = self.bot.language.set_language(interaction=interaction)
    return await self.bot.command.return_autocompletion(self.choices[langcode], current)

  @app_commands.autocomplete(pet=pet_autocomplete)
  @app_commands.command(name='pet')
  @session_command(command_name='pet')
  async def pet_app_command(self, interaction: discord.Interaction, pet: str):
    self.logger.log('debug', f'[PET] Pet : {pet}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'pet': pet
    }
    session = PetSession(session_data)
    await session.start()
  
  async def setup(self, param_list: Optional[list[dict]] = None):
    if param_list:
      self.choices = param_list
    else:
      self.choices = await self.bot.command.set_choices(['pets']) 

async def setup(bot):
  await bot.add_cog(Pet(bot))