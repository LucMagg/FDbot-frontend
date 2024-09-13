import discord
from discord.ext import commands
from discord import app_commands
import requests

from utils.message import Message
from utils.sendMessage import SendMessage
from utils.str_utils import slug_to_str, str_to_slug
from utils.misc_utils import stars

from utils.logger import Logger
from config import DB_PATH


class Petlist(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'petlist'), None)
    self.error_msg = Message(bot).message('error')

    if self.command:
      self.petlist_app_command.name = self.command['name']
      self.petlist_app_command.description = self.command['description']
      self.petlist_app_command._params['héros'].description = self.command['options'][0]['description']


  @app_commands.command(name='petlist')
  async def petlist_app_command(self, interaction: discord.Interaction, héros: str):
    Logger.command_log('petlist', interaction)
    await self.send_message.post(interaction)
    response = Petlist.get_response(self, héros)
    await self.send_message.update(interaction, response)
    Logger.ok_log('petlist')

  def get_response(self, héros):
    if str_to_slug(héros) == 'help':
      return Message(self.bot).help('petlist')
    
    hero = Petlist.get_hero(héros)
    if 'error' not in hero.keys():
      pets = Petlist.get_pets_by_hero(hero['name'])

      if isinstance(pets, list):
        response = {'title': '', 'description': Petlist.description(hero, pets), 'color': 'default', 'pic': hero['image_url']}
      else:
        description = f"{self.error_msg['description']['petlist'][0]['text']} {hero['name']} {self.error_msg['description']['petlist'][1]['text']}"
        response = {'title': self.error_msg['title'], 'description': description, 'color': self.error_msg['color']}
    return response
  
  def get_hero(whichone):
    hero = requests.get(f'{DB_PATH}hero/{slug_to_str(whichone)}')
    return hero.json()
  
  def get_pets_by_hero(whichone):
    pets = requests.get(f'{DB_PATH}pet/hero?hero={whichone}')
    return pets.json()
  
  def description(hero, pets):
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
  

async def setup(bot):
  await bot.add_cog(Petlist(bot))