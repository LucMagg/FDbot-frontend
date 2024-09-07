import discord
from discord.ext import commands
from discord import app_commands
import requests
from utils.message import Message

from utils.sendMessage import SendMessage
from utils.str_utils import str_to_slug
from utils.misc_utils import stars, rank_text, pluriel

from utils.logger import Logger
from config import DB_PATH


class Talent(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'talent'), None)
    self.error_msg = next((m for m in bot.static_data.messages if m['name'] == 'error'), None)

    if self.command:
      self.talent_app_command.name = self.command['name']
      self.talent_app_command.description = self.command['description']
      self.talent_app_command._params['talent'].description = self.command['options'][0]['description']


  @app_commands.command(name='talent')
  async def talent_app_command(self, interaction: discord.Interaction, talent: str):
    Logger.command_log('talent', interaction)
    await self.send_message.post(interaction)
    response = Talent.get_response(self, talent)
    await self.send_message.update(interaction, response)
    Logger.ok_log('talent')

  def get_response(self, talent):
    talent_item = Talent.get_talent(talent)
    if not 'error' in talent_item.keys():
      heroes = Talent.get_heroes_by_talent(talent_item['name'])
      pets = Talent.get_pets_by_talent(talent_item['name'])
      response = {'title': '', 'description': Talent.description(self, talent_item, heroes, pets), 'color': 'default', 'pic': talent_item['image_url']}
    else:
      description = f"{self.error_msg['description']['talent'][0]['text']} {talent} {self.error_msg['description']['talent'][1]['text']}"
      response = {'title': self.error_msg['title'], 'description': description, 'color': self.error_msg['color'], 'pic': None}
    return response
  
  def get_talent(whichone):
    talent = requests.get(f'{DB_PATH}talent/{str_to_slug(whichone)}')
    return talent.json()
  
  def get_heroes_by_talent(whichone):
    heroes = requests.get(f'{DB_PATH}hero/talent?talent={str_to_slug(whichone)}')
    return heroes.json()
  
  def get_pets_by_talent(whichone):
    pets = requests.get(f'{DB_PATH}pet/talent?talent={str_to_slug(whichone)}')
    return pets.json()
  
  def description(self, talent, heroes, pets):
    to_return = Talent.print_header(talent)

    if isinstance(heroes, list):
      to_return += Talent.print_sorted_list('Héros', talent['name'], heroes)
    if isinstance(pets, list):
      to_return += Talent.print_sorted_list('Pets', talent['name'], pets)

    print(len(to_return))

    return to_return
  
  def print_header(talent):
    to_return = f"# {talent['name']} #\n"
    if talent['description'] != '':
      to_return += f"{talent['description']}\n"
    print(to_return)
    return to_return

  def print_sorted_list(whichone, talent_name, list):
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
  

async def setup(bot):
  await bot.add_cog(Talent(bot))