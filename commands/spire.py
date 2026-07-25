import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from utils.session_decorator import session_command
from sessions.spire_add import SpireAddSession
from sessions.spire_details import SpireDetailsSession

from utils.misc_utils import nick


class Spire(commands.Cog):
  spire = app_commands.Group(name='spire', description='...')

  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger

  @spire.command(name='add')
  @session_command(command_name='spire add', oneshot=False)
  async def spireadd_app_command(self, interaction: discord.Interaction, screenshot: Optional[discord.Attachment] = None):
    self.logger.log_only('debug', f'[SPIRE ADD] Screenshot url : {screenshot.url if screenshot else 'no screenshot'} | User : {nick(interaction)}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'screenshot': screenshot
    }
    session = SpireAddSession(session_data)
    await session.start()

  @spire.command(name='details')
  @session_command(command_name='spire details', oneshot=False)
  async def spiredetails_app_command(self, interaction: discord.Interaction):
    self.logger.log_only('debug', f'[SPIRE DETAILS] User : {nick(interaction)}')
    session_data = {
      'cog': self,
      'interaction': interaction
    }
    session = SpireDetailsSession(session_data)
    await session.start()

async def setup(bot):
  await bot.add_cog(Spire(bot))