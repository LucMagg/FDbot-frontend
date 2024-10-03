import discord
from discord.ext import commands
from discord import app_commands
import typing

from utils.message import Message
from utils.sendMessage import SendMessage
from utils.str_utils import str_to_slug
from utils.misc_utils import stars
from service.command import CommandService


class Petlist(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'petlist'), None)
    self.error_msg = Message(bot).message('error')
    self.help_msg = Message(bot).help('petlist')

    self.command_service = CommandService()
    CommandService.init_command(self.petlist_app_command, self.command)
    self.choices = None

  async def héros_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await self.command_service.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(héros=héros_autocomplete)
  @app_commands.command(name='petlist')
  async def petlist_app_command(self, interaction: discord.Interaction, héros: str):
    self.logger.command_log('petlist', interaction)
    self.logger.log_only('debug', f"arg : {héros}")
    await self.send_message.post(interaction)
    response = await self.get_response(héros, interaction)
    await self.send_message.update(interaction, response)
    self.logger.ok_log('petlist')

  async def get_response(self, héros, interaction):
    if str_to_slug(héros) == 'help':
      return self.help_msg
    
    hero = await self.bot.back_requests.call('getHeroByName', True, [héros], interaction)
    if not hero:
      return
    
    pets = await self.bot.back_requests.call('getPetsByHeroname', False, [hero['name']])
    if not pets:
      return {'title': self.error_msg['title'],
              'description': f"{self.error_msg['description']['petlist'][2]['text']} {hero['name']} {self.error_msg['description']['petlist'][3]['text']}",
              'color': self.error_msg['color']}
    
    return {'title': '', 'description': self.description(hero, pets), 'color': hero['color'], 'pic': hero['image_url']}
   
  def description(self, hero, pets):
    to_return = f"# Liste des pets équipables par {hero['name']} #\n"
    to_return += Petlist.print_sorted_list(hero, pets)
    return to_return

  def print_sorted_list(hero, pets):
    list = sorted(pets, key = lambda p: (p['stars'], p['name']))
    to_return = ''

    star = 0
    for l in list:
      if star != l['stars']:
        star = l['stars']
        to_return += f"### {stars(l['stars'])} ###\n"

      to_return += f"{l['name']} : +{l['attack']}% att/def"

      if l['petclass'] == hero['heroclass']:
        full_talent = next((t for t in l['talents'] if t['position'] == 'full'), None)
        if full_talent['name'] is not None:
          to_return += f" + {full_talent['name']} (full)"
      
      if l['signature'] == hero['name'] or l['signature_bis'] == hero['name']:
        gold_talent = next((t for t in l['talents'] if t['position'] == 'gold'), None)
        to_return += f" + {gold_talent['name']} (gold) pour {l['manacost']} mana"
        
      to_return += '\n'

    return to_return
  
  async def setup(self, param_list):
    if param_list is None:
      choices = await self.bot.back_requests.call('getAllHeroes', False)
    else:
      choices = param_list
    self.choices = CommandService.set_choices(choices) 
  

async def setup(bot):
  await bot.add_cog(Petlist(bot))