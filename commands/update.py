import discord
from discord.ext import commands
from discord import app_commands
import requests
from typing import Literal

from utils.message import Message
from utils.sendMessage import SendMessage
from utils.str_utils import str_to_slug

from utils.logger import Logger
from config import DB_PATH

UpdateTypes = Literal['Héros','Pets','Talents','Tout']

class Update(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'update'), None)
    self.error_msg = Message(bot).message('error')
    self.return_msg = Message(bot).message('update')
    self.help_msg = Message(bot).help('update')

    if self.command:
      self.update_app_command.name = self.command['name']
      self.update_app_command.description = self.command['description']


  @app_commands.command(name='update')
  async def update_app_command(self, interaction: discord.Interaction):
    Logger.command_log('update', interaction)
    await self.send_message.post(interaction, self.return_msg['description']['warning'])
    response = Update.get_response(self, type)
    await self.send_message.update(interaction, response)
    Logger.ok_log('update')

  def get_response(self):
    print('here')
    update = requests.get(f'{DB_PATH}update')
    if 'error' not in update.keys():
      description = self.return_msg['description']['all']
    else:
      description = self.return_msg['description']['erreur']
    return {'title': self.return_msg['title'], 'description': description, 'color': 'default'}
  
async def setup(bot):
  await bot.add_cog(Update(bot))