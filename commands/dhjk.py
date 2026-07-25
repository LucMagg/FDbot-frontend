import os
import discord
from discord.ext import commands
from discord import app_commands

from utils.session_decorator import session_command
from sessions.dhjk import DhjkSession


class Dhjk(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.image_path = 'images/gifs'
    self.images = self._get_images()

  @app_commands.command(name='dhjk')
  @session_command(command_name='dhjk')
  async def dhjk_app_command(self, interaction: discord.Interaction):
    session_data = {
      'cog': self,
      'interaction': interaction
    }
    session = DhjkSession(session_data)
    await session.start()
  
  def _get_images(self) -> list:
    images = []
    if not os.path.isdir(self.image_path):
      self.logger.log_only('warning', f'[DHJK] Unable to find folder : {self.image_path}')
      return images
    for filename in os.listdir(self.image_path):
      if filename.lower().endswith('.gif'):
        images.append(os.path.join(self.image_path, filename))
    if not images:
      self.logger.log_only('warning', f'[DHJK] No GIF found in {self.image_path}')
    return images
  
async def setup(bot):
  await bot.add_cog(Dhjk(bot))