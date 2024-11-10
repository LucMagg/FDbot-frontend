import discord
from discord.ext import commands
from discord import app_commands
import random

from utils.sendMessage import SendMessage
from utils.misc_utils import stars
from service.command import CommandService


class Dhjk(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'dhjk'), None)
    self.messages = next((m for m in bot.static_data.messages if m['name'] == 'dhjk'), None)

    self.command_service = CommandService()
    CommandService.init_command(self.dhjk_app_command, self.command)


  @app_commands.command(name='dhjk')
  async def dhjk_app_command(self, interaction: discord.Interaction):
    self.logger.command_log('dhjk', interaction)
    await self.send_message.handle_response(interaction=interaction, wait_msg=True)
    response = Dhjk.get_response(self)
    await self.send_message.handle_response(interaction=interaction, response=response)
    self.logger.ok_log('dhjk')

  def get_response(self):
    rand = random.randint(0, 4)
    return {'title': stars(10), 'description': self.messages['items'][rand]['text'], 'color': 'blue', 'image': self.messages['items'][rand]['gif']}
  
async def setup(bot):
  await bot.add_cog(Dhjk(bot))