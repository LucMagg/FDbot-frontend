import discord
from discord.ext import commands
from discord import app_commands
import requests

from utils.message import Message
from utils.sendMessage import SendMessage
from utils.str_utils import slug_to_str, str_to_slug
from utils.misc_utils import stars, rank_text

from utils.logger import Logger
from config import DB_PATH


class Classe(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'class'), None)
    self.error_msg = Message(bot).message('error')

    if self.command:
      self.classe_app_command.name = self.command['name']
      self.classe_app_command.description = self.command['description']
      self.classe_app_command._params['classe'].description = self.command['options'][0]['description']


  @app_commands.command(name='class')
  async def classe_app_command(self, interaction: discord.Interaction, classe: str):
    Logger.command_log('class', interaction)
    await self.send_message.post(interaction)
    response = Classe.get_response(self, classe)
    await self.send_message.update(interaction, response)
    Logger.ok_log('class')

  def get_response(self, classe):
    if str_to_slug(classe) == 'help':
      classes = Classe.get_all_classes()
      if classes:
        class_list = '\n'.join([f"* {c['heroclass']}" for c in classes])
        help_msg = Message(self.bot).help('class', class_list)
      return help_msg
    
    heroes = Classe.get_heroes_by_class(classe)
    pets = Classe.get_pets_by_class(classe)

    if not (isinstance(heroes, list) or isinstance(pets, list)):
      description = f"{self.error_msg['description']['class'][0]['text']} {classe} {self.error_msg['description']['class'][1]['text']}"
      return {'title': self.error_msg['title'], 'description': description, 'color': self.error_msg['color'], 'pic': None}
    
    response = {'title': '', 'description': Classe.description(self, classe, heroes, pets), 'color': 'default', 'pic': None}  
    return response
  
  def get_heroes_by_class(whichone):
    heroes = requests.get(f'{DB_PATH}hero/class?class={slug_to_str(whichone)}')
    return heroes.json()
  
  def get_pets_by_class(whichone):
    pets = requests.get(f'{DB_PATH}pet/class?class={slug_to_str(whichone)}')
    return pets.json()

  def get_all_classes():
    classes = requests.get(f"{DB_PATH}hero/class?class=all")
    return classes.json()
  
  def description(self, classe, heroes, pets):
    to_return = Classe.print_header(classe)

    if isinstance(heroes, list):
      to_return += Classe.print_sorted_list('Héros', heroes)
    if isinstance(pets, list):
      to_return += Classe.print_sorted_list('Pets', pets)

    return to_return
  
  def print_header(classe):
    return f"# {slug_to_str(classe)} #\n"

  def print_sorted_list(whichone, list):
    list = sorted(list, key = lambda l: (l['stars'], l['name']))
    match whichone:
      case 'Héros':
        to_return = '### Liste des héros de la classe spécifiée : ###\n'
      case 'Pets':
        to_return = '### Liste des pets de classe : ###\n'

    star = 0
    for l in list:
      if star != l['stars']:
        star = l['stars']
        to_return += f"### {stars(l['stars'])} ###\n"
      to_return += f"{l['name']} ({l['color']}"

      match whichone:
        case 'Héros':
          to_return += f" {str.lower(l['species'])}) : Attack : {l['att_max']} ({l['att_rank']}{rank_text(l['att_rank'])}) | Defense : {l['def_max']} ({l['def_rank']}{rank_text(l['def_rank'])})\n"
        case 'Pets':
          to_return += f") : {l['signature']}"
          if l['signature_bis'] is not None:
            to_return += f", {l['signature_bis']}\n"
          else:
            to_return += '\n'

    return to_return
  

async def setup(bot):
  await bot.add_cog(Classe(bot))