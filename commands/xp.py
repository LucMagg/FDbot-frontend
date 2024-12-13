import discord
import typing
import math
from discord.ext import commands
from discord import app_commands

from service.xp import XpService
from service.interaction_handler import InteractionHandler
from utils.misc_utils import stars as stars_to_str
from service.command import CommandService


class Xp(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'xp'), None)
    self.xp_data = bot.static_data.xp_data
    self.thresholds = bot.static_data.xp_thresholds
    self.ascends = None

    CommandService.init_command(self.xp_app_command, self.command)

  @app_commands.command(name='xp')
  async def xp_app_command(self, interaction: discord.Interaction, stars: int, current_ascend: str, current_level: int, target_ascend: str, target_level: int):
    self.logger.command_log('xp', interaction)
    self.interaction_handler = InteractionHandler(self.bot)
    await self.interaction_handler.send_wait_message(interaction=interaction)
    response = await self.get_response(stars, current_ascend, current_level, target_ascend, target_level)
    if response:
      await self.interaction_handler.send_embed(interaction=interaction, response=response)
    self.logger.ok_log('xp')

  async def get_response(self, stars, current_ascend, current_level, target_ascend, target_level):
    threshold_table = next((d for d in self.thresholds if d.get('hero_stars') == stars), None)

    error = XpService.check_errors(threshold_table, stars, current_ascend, current_level, target_ascend, target_level)
    if error:
      return error

    xp_table = next((d.get('data') for d in self.xp_data if d.get('hero_stars') == stars), None)
    xp_str = XpService.calc_xp(xp_table, threshold_table, stars, current_ascend, current_level, target_ascend, target_level)

    return {'title': '', 'description': f'# {stars_to_str(stars)} #\n{xp_str}', 'color': 'blue'}

async def setup(bot):
  await bot.add_cog(Xp(bot))