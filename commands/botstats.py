import discord
from discord.ext import commands
from discord import app_commands
from collections import Counter

from service.command import CommandService
from utils.sendMessage import SendMessage
from utils.misc_utils import stars


class Botstats(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'botstats'), None)
    self.command_service = CommandService()
    CommandService.init_command(self.botstats_app_command, self.command)


  @app_commands.command(name='botstats')
  async def botstats_app_command(self, interaction: discord.Interaction):
    self.logger.command_log('botstats', interaction)
    await self.send_message.handle_response(interaction=interaction, wait_msg=True)
    response = await self.get_response()
    await self.send_message.handle_response(interaction=interaction, response=response)
    self.logger.ok_log('botstats')

  async def get_response(self):
    talents = await self.bot.back_requests.call('getAllTalents', False)
    heroes = await self.bot.back_requests.call('getAllHeroes', False)
    pets = await self.bot.back_requests.call('getAllPets', False)

    response = {'title': '', 'description': Botstats.description(talents, heroes, pets), 'color': 'default'}
    return response
  
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