import discord
from discord.ext import commands
from discord import app_commands
import requests
from collections import Counter

from utils.sendMessage import SendMessage
from utils.misc_utils import stars
from utils.logger import Logger
from config import DB_PATH

class Botstats(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'botstats'), None)

    if self.command:
      self.botstats_app_command.name = self.command['name']
      self.botstats_app_command.description = self.command['description']


  @app_commands.command(name='botstats')
  async def botstats_app_command(self, interaction: discord.Interaction):
    Logger.command_log('botstats', interaction)
    await self.send_message.post(interaction)
    response = Botstats.get_response()
    await self.send_message.update(interaction, response)
    Logger.ok_log('botstats')

  def get_response():
    talents = Botstats.get_talents()
    heroes = Botstats.get_heroes()
    pets = Botstats.get_pets()

    response = {'title': '', 'description': Botstats.description(talents, heroes, pets), 'color': 'default'}
    return response
  
  def get_talents():
    talent = requests.get(f'{DB_PATH}talent')
    return talent.json()
  
  def get_heroes():
    heroes = requests.get(f'{DB_PATH}hero')
    return heroes.json()
  
  def get_pets():
    pets = requests.get(f'{DB_PATH}pet')
    return pets.json()
  
  def description(talents, heroes, pets):
    description = '# Stats du bot #\n'
    
    description += f"### {len(heroes)} héros recensés : ###\n* "
    description += Botstats.detailed_count(heroes, 'heroclass')
    description += '\n'

    description += f"### {len(pets)} pets recensés : ###\n* "
    description += Botstats.detailed_count(pets, 'petclass')
    description += '\n'

    description += f"### {len(talents)} talents recensés ###\n"

    return description


  def detailed_count(list, whichone):
    to_return = ''
    list_stars_count = Counter(l['stars'] for l in list)
    l_stars_print = []
    for k, v in sorted(list_stars_count.items()):
      l_stars_print.append(f"{v} {stars(k)}")
    to_return += ', '.join(l_stars_print)
    to_return += '\n'

    list_colors_count = Counter(l['color'] for l in list)
    to_return += f"* {len(list_colors_count)} couleurs ("
    l_colors_print = []
    for k, v in sorted(list_colors_count.items()):
      l_colors_print.append(f"{v} {k}")
    to_return += ', '.join(l_colors_print)
    to_return += ')\n'

    if whichone == 'heroclass':
      list_species_count = Counter(l['species'] for l in list)
      to_return += f"* {len(list_species_count)} espèces ("
      l_species_print = []
      for k, v in sorted(list_species_count.items()):
        l_species_print.append(f"{v} {k}")
      to_return += ', '.join(l_species_print)
      to_return += ')\n'

    list_classes_count = Counter(l[whichone] for l in list)
    to_return += f"* {len(list_classes_count)} classes ("
    l_classes_print = []
    for k, v in sorted(list_classes_count.items()):
      l_classes_print.append(f"{v} {k}")
    to_return += ', '.join(l_classes_print)
    to_return += ')\n'

    return to_return
  
async def setup(bot):
  await bot.add_cog(Botstats(bot))