import discord
import typing
from discord.ext import commands
from discord import app_commands

from service.interaction_handler import InteractionHandler
from service.command import CommandService

from utils.misc_utils import stars


class Merclist(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'merclist'), None)
    self.xp_data = bot.static_data.xp_data
    self.thresholds = bot.static_data.xp_thresholds
    self.ascends = None

    CommandService.init_command(self.merclist_app_command, self.command)
    self.choices = None

  async def user_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await CommandService.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(user=user_autocomplete)
  @app_commands.command(name='merclist')
  async def merclist_app_command(self, interaction: discord.Interaction, user: str):
    self.logger.command_log('merclist', interaction)
    self.interaction_handler = InteractionHandler(self.bot)
    await self.interaction_handler.send_wait_message(interaction=interaction)
    response = await self.bot.merc_service.get_all_mercs_by_user_id(user)
    if response:
      await self.interaction_handler.send_embed(interaction=interaction, response=response)
    self.logger.ok_log('merclist')
  
  async def setup(self, param_list):
    if param_list is None:
      choices = await self.bot.back_requests.call('getAllMercUsers', False)
      if choices:
        choices = [{'name': c.get('user'), 'name_slug': str(c.get('user_id'))} for c in choices]
      else:
        choices = []
    else:
      choices = param_list
    self.choices = CommandService.set_choices(choices)

async def setup(bot):
  await bot.add_cog(Merclist(bot))