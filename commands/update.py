import discord
from discord.ext import commands
from discord import app_commands
import typing

from utils.message import Message
from utils.sendMessage import SendMessage
from service.command import CommandService


class Update(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'update'), None)
    self.error_msg = Message(bot).message('error')
    self.return_msg = Message(bot).message('update')
    self.help_msg = Message(bot).help('update')

    CommandService.init_command(self.update_app_command, self.command, no_choices=True)
    self.choices = self.get_choices()

  def get_choices(self):
    return [app_commands.Choice(name=c['name'], value=c['value']) for c in self.command['options'][0]['choices']]
  
  async def type_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return [c for c in self.choices if current.lower() in c.name.lower()]

  @app_commands.autocomplete(type=type_autocomplete)
  @app_commands.command(name='update')
  async def update_app_command(self, interaction: discord.Interaction, type: str):
    self.logger.command_log('update', interaction)
    self.logger.log_only('debug', f"arg : {type}")
    await self.send_message.handle_response(interaction=interaction, wait_msg=True, more_response=self.return_msg['description']['warning'])
    if not type:
      type = 'all'
    
    response = await self.get_response(type, interaction)
    await self.send_message.handle_response(interaction=interaction, response=response)
    self.logger.ok_log('update')


  async def get_response(self, type, interaction):
    if type == 'help':
      return self.help_msg
    
    if type == 'all':
      update = await self.bot.back_requests.call('getAllUpdates', False)
    else:
      update = await self.bot.back_requests.call('getOneUpdate', False, [type])

    if not update:
      return {'title': self.return_msg['title'], 'description': self.return_msg['description']['erreur'], 'color': 'default'}
    
    if type == 'all':
      description = f"{self.return_msg['description']['all']}{self.return_msg['description']['thxmsg']}"
      types_to_update = ['hero', 'pet', 'talent']
    else:
      type_name = next((c['name'].lower() for c in self.command['options'][0]['choices'] if c['value'] == type), None)
      description = f"{self.return_msg['description']['part1']} {type_name} {self.return_msg['description']['part2']}{self.return_msg['description']['thxmsg']}"
      types_to_update = [type]
      
    await self.bot.update_service.command_setup_updater(types_to_update, True)    
    return {'title': self.return_msg['title'], 'description': description, 'color': 'default'}


async def setup(bot):
  await bot.add_cog(Update(bot))