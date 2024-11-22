import discord
from discord.ext import commands
from discord import app_commands
import typing

from utils.message import Message
from service.interaction_handler import InteractionHandler
from utils.str_utils import slug_to_str, str_to_slug
from utils.misc_utils import stars, rank_text
from service.command import CommandService


class Classe(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.interaction_handler = InteractionHandler(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'class'), None)

    CommandService.init_command(self.classe_app_command, self.command)
    self.choices = None

  async def classe_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await CommandService.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(classe=classe_autocomplete)
  @app_commands.command(name='class')
  async def classe_app_command(self, interaction: discord.Interaction, classe: str):
    self.logger.command_log('class', interaction)
    self.logger.log_only('debug', f"arg : {classe}")
    await self.interaction_handler.handle_response(interaction=interaction, wait_msg=True)
    response = await self.get_response(classe, interaction)
    if response:
      await self.interaction_handler.handle_response(interaction=interaction, response=response)
    self.logger.ok_log('class')

  async def get_response(self, classe, interaction):
    if str_to_slug(classe) == 'help':
      class_list = '\n'.join([f"* {c.name}" for c in self.choices])
      help_msg = Message(self.bot).help('class', class_list)
      return help_msg
    
    pets = await self.bot.back_requests.call('getPetsByClass', False, [classe])
    heroes = await self.bot.back_requests.call('getHeroesByClass', True, [classe], interaction)
    
    if not heroes:
      return
    
    response = {'title': '', 'description': self.description(classe, heroes, pets), 'color': 'default'}  
    return response
  
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
  
  async def setup(self, param_list):
    if param_list is None:
      choices = await self.bot.back_requests.call('getAllClasses', False)
    else:
      choices = param_list
    self.choices = CommandService.set_choices([{'name': c['heroclass']} for c in choices]) 
  

async def setup(bot):
  await bot.add_cog(Classe(bot))