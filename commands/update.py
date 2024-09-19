import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
import requests
import typing

from utils.message import Message
from utils.sendMessage import SendMessage
from utils.str_utils import str_to_slug

from utils.logger import Logger
from config import DB_PATH


class Update(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'update'), None)
    self.error_msg = Message(bot).message('error')
    self.return_msg = Message(bot).message('update')
    self.help_msg = Message(bot).help('update')
    self.known_types = self.get_known_types()

    if self.command:
      self.update_app_command.name = self.command['name']
      self.update_app_command.description = self.command['description']
      self.update_app_command._params['type'].description = self.command['options'][0]['description']
      self.update_app_command._params['type'].required = self.command['options'][0]['required']
      #self.update_app_command._params['type'].choices = [Choice(name=c['name'], value=c['type']) for c in self.command['options'][0]['choices']]

  def get_known_types(self):
    return [app_commands.Choice(name=t['name'], value=t['type']) for t in self.command['options'][0]['choices']]

  async def type_autocompletion(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return [t for t in self.known_types if current.lower() in t.name.lower()]

  @app_commands.command(name='update')
  @app_commands.autocomplete(type=type_autocompletion)
  async def update_app_command(self, interaction: discord.Interaction, type: str):
    Logger.command_log('update', interaction)
    await self.send_message.post(interaction, self.return_msg['description']['warning'])
    if not type:
      type = Choice(name='Tout', value='all')
    print(type)
    
    response = Update.get_response(self, type)
    await self.send_message.update(interaction, response)
    Logger.ok_log('update')

  def get_response(self, type):
    if type == 'help':
      return self.help_msg
    if type == 'all':
      update = requests.get(f'{DB_PATH}update').json()
    else:
      update = requests.get(f'{DB_PATH}update?type={type}').json()

    if 'error' not in update.keys():
      if type == 'all':
        description = f"{self.return_msg['description']['all']}{self.return_msg['description']['thxmsg']}"
      else:
        description = f"{self.return_msg['description']['part1']} {type} {self.return_msg['description']['part2']}{self.return_msg['description']['thxmsg']}"
    else:
      description = self.return_msg['description']['erreur']
          
    return {'title': self.return_msg['title'], 'description': description, 'color': 'default'}
  
async def setup(bot):
  await bot.add_cog(Update(bot))