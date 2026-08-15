import discord
from discord.ext import commands
from discord import app_commands

from utils.session_decorator import session_command
from sessions.update import UpdateSession
from ui.base_ui import BaseUiData


class Update(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger

  @app_commands.command(name='update')
  @session_command(command_name='update', oneshot=False)
  async def update_app_command(self, interaction: discord.Interaction, type: str):
    self.logger.log_only('debug', f'[UPDATE] Type : {type}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'type': type
    }
    session = UpdateSession(session_data)
    await session.start()

async def setup(bot):
  await bot.add_cog(Update(bot))