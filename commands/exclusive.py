import discord
from discord.ext import commands
from discord import app_commands
import typing

from utils.message import Message
from service.interaction_handler import InteractionHandler
from utils.str_utils import str_to_slug
from utils.misc_utils import pluriel
from service.command import CommandService


class Exclusive(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.interaction_handler = InteractionHandler(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'exclusive'), None)
    CommandService.init_command(self.exclusive_app_command, self.command)
    self.choices = None

  async def type_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await CommandService.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(type=type_autocomplete)
  @app_commands.command(name='exclusive')
  async def exclusive_app_command(self, interaction: discord.Interaction, type: str):
    self.logger.command_log('exclusive', interaction)
    self.logger.log_only('debug', f"arg : {type}")
    await self.interaction_handler.handle_response(interaction=interaction, wait_msg=True)
    response = await self.get_response(type, interaction)
    if response:
      await self.interaction_handler.handle_response(interaction=interaction, response=response)
    self.logger.ok_log('exclusive')

  async def get_response(self, type, interaction):
    if str_to_slug(type) == 'help':
      help_msg = Message(self.bot).help('exclusive')
      return help_msg
    
    if str_to_slug(type) == 'tous':
      type = None
    
    exclusive_heroes = await self.bot.back_requests.call('getExclusiveHeroes', True, [{'type': type}], interaction)
    if not exclusive_heroes:
      return
    
    response = {'title': '', 'description': self.description(type, exclusive_heroes), 'color': 'default'}  
    return response
  
  def description(self, type, exclusive_heroes):
    to_return = self.print_header(type, exclusive_heroes)
    print(to_return)
    for heroes_list in exclusive_heroes:
      if type is None:
        to_return += f'### {heroes_list.get('exclusive')} Exclusives ###\n'
      for hero in heroes_list.get('heroes'):
        to_return += f'{hero.get('name')} ({hero.get('stars')}:star: {hero.get('color')} {hero.get('species').lower()} {hero.get('heroclass').lower()})\n'
      print(to_return)
    return to_return
  
  def print_header(self, type, exclusive_heroes):
    print(exclusive_heroes[0].get('heroes'))
    if type is not None:
      return f'# {type} Exclusive{pluriel(exclusive_heroes[0].get('heroes'))} #\n'
    return f'# Liste des héros exclusifs #\n'
  
  async def setup(self, param_list):
    if param_list is None:
      choices = await self.bot.back_requests.call('getExclusiveTypes', False)
    else:
      choices = param_list
    choices.append('Tous')
    #choices.append('Help')
    choices = sorted(choices)

    self.choices = CommandService.set_choices([{'name': c} for c in choices]) 

async def setup(bot):
  await bot.add_cog(Exclusive(bot))