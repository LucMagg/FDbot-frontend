import discord
from discord.ext import commands
from discord import app_commands
import random

from utils.sendMessage import SendMessage
from utils.misc_utils import stars

from utils.logger import Logger

class Dhjk(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'dhjk'), None)
    self.messages = next((m for m in bot.static_data.messages if m['name'] == 'dhjk'), None)

    if self.command:
      self.dhjk_app_command.name = self.command['name']
      self.dhjk_app_command.description = self.command['description']


  @app_commands.command(name='class')
  async def dhjk_app_command(self, interaction: discord.Interaction):
    Logger.command_log('dhjk', interaction)
    await self.send_message.post(interaction)
    response = Dhjk.get_response(self)
    await self.send_message.update(interaction, response)
    Logger.ok_log('dhjk')

  def get_response(self):
    rand = random.randint(0, 4)
    return {'title': stars(10), 'description': self.messages['items'][rand]['text'], 'color': 'blue', 'image': self.messages['items'][rand]['gif']}
  
async def setup(bot):
  await bot.add_cog(Dhjk(bot))