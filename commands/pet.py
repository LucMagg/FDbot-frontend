import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import typing

from service.command import CommandService
from utils.message import Message
from utils.sendMessage import SendMessage
from utils.str_utils import str_to_slug
from utils.misc_utils import stars, pluriel


class Pet(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'pet'), None)
    self.help_msg = Message(bot).help('pet')

    self.command_service = CommandService()
    CommandService.init_command(self.pet_app_command, self.command)
    self.choices = None

  async def pet_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await self.command_service.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(pet=pet_autocomplete)
  @app_commands.command(name='pet')
  async def pet_app_command(self, interaction: discord.Interaction, pet: str):
    self.logger.command_log('pet', interaction)
    self.logger.log_only('debug', f"arg : {pet}")
    await self.send_message.post(interaction)
    response = await self.get_response(pet, interaction)
    await self.send_message.update(interaction, response)
    self.logger.ok_log('pet')

  async def get_response(self, pet, interaction):
    if str_to_slug(pet) == 'help':
      return self.help_msg
    
    pet_item = await self.bot.back_requests.call('getPetByName', True, [pet], interaction)
    if not pet_item:
      return

    return {'title': '', 'description': await self.description(pet_item), 'color': pet_item['color'], 'pic': pet_item['image_url']}
   
  async def description(self, pet):
    return self.print_header(pet) + self.print_stats(pet) + self.print_signature(pet) + await self.print_full_talent(pet) + await self.print_talents(pet) + self.print_comments(pet, Message(self.bot))
  
  def print_header(self, pet):
    return f"# {pet['name']}   {stars(pet['stars'])} #\n{pet['color']} pet pour {str.lower(pet['petclass'])}\n"
  
  def print_stats(self, pet):
    to_return = '### Attributs max : ###\n'
    to_return += f"+ {pet['attack']}% attaque/défense\n"
    return to_return
  
  def print_signature(self, pet):
    to_return = '### Héros signature : ###\n'
    to_return += pet['signature']
    if pet['signature_bis'] is not None:
      to_return += f" | {pet['signature_bis']}"
    to_return += '\n'
    return to_return
  
  async def print_full_talent(self, pet):
    heroes = await self.bot.back_requests.call('getHeroesByPet', False, [pet.get('name')])
    if heroes:
      heroes = [h['name'] for h in heroes if h['name'] != pet['signature']]
      if len(heroes) > 0:
        pl = pluriel(heroes)
        to_return = f"### Autre{pl} héros pouvant bénéficier du full talent : ###\n"
        to_return += f"{', '.join(heroes)}\n"
        return to_return
    return ''
  
  async def print_talents(self, pet):
    merge_talents = []
    for i in range(1, 11):
      for t in pet['talents']:
        if ' ' in t['position']:
          pos = t['position'].split(' ')
          if int(pos[1]) == i:
            merge_talents.append(t['name'])

    manacost_merge = sum(1 for t in pet['talents'] if t['name'] == 'Mana Efficiency')

    to_return = '### Talents : ###\n'
    to_return += f"__**Base :**__\n{next((t['name'] for t in pet['talents'] if t['position'] == 'base'), None)} (+1% att/def)\n"
    to_return += f"__**Silver :**__\n{next((t['name'] for t in pet['talents'] if t['position'] == 'silver'), None)} (+1% att/def)\n"

    full_talent = next((t['name'] for t in pet['talents'] if t['position'] == 'full'), None)
    to_return += f"__**Full :**__\n{full_talent} (seulement pour les {str.lower(pet['petclass'])}s)\n"
    to_return += f"__**Merge :**__\n{' | '.join(merge_talents)}\n"
    
    gold_talent = next((t for t in pet['talents'] if t['position'] == 'gold'), None)
    to_return += f"__**Gold :**__\n{gold_talent['name']}\n"

    talent = await self.bot.back_requests.call('getTalentByName', False, [gold_talent['name']])
    to_return += f"-> {talent['description']}\n"
    to_return += f"__**Mana Cost :**__\n25 (base) - {25 - pet['manacost'] - manacost_merge} (gold) - {manacost_merge} (merge) = **{pet['manacost']}**\n"
    return to_return

  def print_comments(self, pet, message):
    to_return = f"### Commentaire{pluriel(pet['comments'])} : ###\n"
    if len(pet['comments']) > 0:
      for comment in pet['comments']:
        my_date = datetime.strptime(comment['date'], "%a, %d %b %Y %H:%M:%S %Z").strftime("%d/%m/%Y")
        to_return += f"__{comment['author']} le {my_date}__\n"
        to_return += f"{comment['commentaire']}\n"
    else :
      nocomment = message.message('nocomment')
      to_return += nocomment['description']
    return to_return
  
  async def setup(self, param_list):
    if param_list is None:
      choices = await self.bot.back_requests.call('getAllPets', False)
    else:
      choices = param_list
    self.choices = CommandService.set_choices(choices) 

async def setup(bot):
  await bot.add_cog(Pet(bot))