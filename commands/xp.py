import discord
from discord.ext import commands
from discord import app_commands

from utils.session_decorator import session_command
from sessions.xp import XpSession


class Xp(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.xp_data = bot.static_data.xp_data
    self.thresholds = bot.static_data.xp_thresholds
    self.ascends = None

  @app_commands.command(name='xp')
  @session_command(command_name='xp')
  async def xp_app_command(self, interaction: discord.Interaction, stars: int, current_ascend: str, current_level: int, target_ascend: str, target_level: int):
    self.logger.log('debug', f'[XP] stars : {stars} | current_ascend : {current_ascend} | current_level : {current_level} | target_ascend : {target_ascend} | target_level : {target_level}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'stars': int(stars),
      'current_ascend': current_ascend,
      'current_level': int(current_level),
      'target_ascend': target_ascend,
      'target_level': int(target_level)
    }
    session = XpSession(session_data)
    await session.start()

async def setup(bot):
  await bot.add_cog(Xp(bot))