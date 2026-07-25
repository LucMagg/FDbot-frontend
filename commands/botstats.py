import discord
from discord.ext import commands
from discord import app_commands

from utils.session_decorator import session_command
from sessions.botstats import BotStatsSession


class Botstats(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger

  @app_commands.command(name='botstats')
  @session_command(command_name='botstats')
  async def botstats_app_command(self, interaction: discord.Interaction):
    session_data = {
      'cog': self,
      'interaction': interaction
    }
    session = BotStatsSession(session_data)
    await session.start()
  
async def setup(bot):
  await bot.add_cog(Botstats(bot))