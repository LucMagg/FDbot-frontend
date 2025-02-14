import discord
from discord.ext import commands
from discord import app_commands
import typing

from utils.message import Message
from service.interaction_handler import InteractionHandler
from utils.str_utils import str_to_slug
from utils.misc_utils import stars
from service.command import CommandService



class Talent(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'talent'), None)
    self.help_msg = Message(bot).help('talent')

    CommandService.init_command(self.talent_app_command, self.command)
    self.choices = None

  async def talent_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await CommandService.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(talent=talent_autocomplete)
  @app_commands.command(name='talent')
  async def talent_app_command(self, interaction: discord.Interaction, talent: str):
    self.logger.command_log('talent', interaction)
    self.logger.log_only('debug', f"arg : {talent}")
    self.interaction_handler = InteractionHandler(self.bot)
    await self.interaction_handler.send_wait_message(interaction=interaction)
    response = await self.get_response(talent, interaction)
    await self.interaction_handler.send_embed(interaction=interaction, response=response)
    self.logger.ok_log('talent')

  async def get_response(self, talent, interaction):
    print(talent)
    if str_to_slug(talent) == 'help':
      return self.help_msg
    
    talent_item = await self.bot.back_requests.call('getTalentByName', True, [talent], interaction)
    if not talent_item:
      return
    
    heroes = await self.bot.back_requests.call('getHeroesByTalent', False, [talent_item.get('name')])
    pets = await self.bot.back_requests.call('getPetsByTalent', False, [talent_item.get('name')])

    return {'title': '', 'description': self.description(talent_item, heroes, pets), 'color': 'default', 'pic': talent_item['image_url']}
  
  def description(self, talent, heroes, pets):
    to_return = self.print_header(talent)

    if heroes:
      to_return += self.print_sorted_list('Héros', talent['name'], heroes)
    if pets:
      to_return += self.print_sorted_list('Pets', talent['name'], pets)

    return to_return
  
  def print_header(self, talent):
    to_return = f"# {talent['name']} #\n"
    if talent['description'] is not None:
      to_return += f"{talent['description']}\n"
    return to_return

  def print_sorted_list(self, whichone, talent_name, list):
    list = sorted(list, key = lambda l: (l['stars'], l['name']))
    to_return = f"### {whichone} ayant {talent_name} :###\n"

    star = 0
    for l in list:
      if star != l['stars']:
        star = l['stars']
        to_return += f"### {stars(l['stars'])} ###\n"
      multiple_talents = ''
      if len(l['talents']) > 1:
        multiple_talents = f"x{len(l['talents'])}"
      talents = ', '.join(l['talents'])
      match whichone:
        case 'Héros':
          l_class = 'heroclass'
        case 'Pets':
          l_class = 'petclass'
      to_return += f"{l['name']} ({l['color']} {str.lower(l[l_class])}) {multiple_talents} : {talents}\n"
    return to_return
  
  async def setup(self, param_list):
    if param_list is None:
      choices = await self.bot.back_requests.call('getAllTalents', False)
    else:
      choices = param_list
    self.choices = CommandService.set_choices(choices) 
  

async def setup(bot):
  await bot.add_cog(Talent(bot))