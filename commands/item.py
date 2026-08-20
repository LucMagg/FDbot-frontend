import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from utils.session_decorator import session_command
from sessions.item import ItemSession


class Item(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.choices = None

  async def item_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    langcode = self.bot.language.set_language(interaction=interaction)
    return await self.bot.command.return_autocompletion(self.choices[langcode], current.strip())

  @app_commands.autocomplete(item=item_autocomplete)
  @app_commands.command(name='item')
  @session_command(command_name='item')
  async def item_app_command(self, interaction: discord.Interaction, item: str):
    self.logger.log('debug', f'[ITEM] Item : {item}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'item': item
    }
    session = ItemSession(session_data)
    await session.start()
  
  async def setup(self, param_list: Optional[list[dict]] = None):
    if param_list:
      self.choices = param_list
    else:
      self.choices = await self.bot.command.set_choices(['items'])

async def setup(bot):
  await bot.add_cog(Item(bot))