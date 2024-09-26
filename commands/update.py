import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
import requests
import typing

from utils.message import Message
from utils.sendMessage import SendMessage
from utils.str_utils import str_to_slug
from service.command import CommandService

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

    self.command_service = CommandService()
    CommandService.init_command(self.update_app_command, self.command, no_choices=True)
    self.choices = self.get_choices()

  def get_choices(self):
    return [app_commands.Choice(name=c['name'], value=c['value']) for c in self.command['options'][0]['choices']]
  
  async def type_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return [c for c in self.choices if current.lower() in c.name.lower()]

  @app_commands.autocomplete(type=type_autocomplete)
  @app_commands.command(name='update')
  async def update_app_command(self, interaction: discord.Interaction, type: str):
    Logger.command_log('update', interaction)
    await self.send_message.post(interaction, self.return_msg['description']['warning'])
    if not type:
      type = 'all'
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
        type = next((c['name'].lower() for c in self.command['options'][0]['choices'] if c['value'] == type), None)
        description = f"{self.return_msg['description']['part1']} {type} {self.return_msg['description']['part2']}{self.return_msg['description']['thxmsg']}"
    else:
      description = self.return_msg['description']['erreur']
          
    return {'title': self.return_msg['title'], 'description': description, 'color': 'default'}


async def setup(bot):
  await bot.add_cog(Update(bot))