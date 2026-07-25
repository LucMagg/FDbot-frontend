import discord
from discord.ext import commands
from discord import app_commands

from utils.session_decorator import session_command
from sessions.bothelp import BotHelpSession


class Bothelp(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger

  @app_commands.command(name='bothelp')
  @session_command(command_name='bothelp')
  async def bothelp_app_command(self, interaction: discord.Interaction):
    session_data = {
      'cog': self,
      'interaction': interaction
    }
    session = BotHelpSession(session_data)
    await session.start()
  
async def setup(bot):
  await bot.add_cog(Bothelp(bot))