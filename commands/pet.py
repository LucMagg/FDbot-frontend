import discord
from discord.ext import commands
from discord import app_commands
import requests
from datetime import datetime
import typing

from service.command import CommandService
from utils.message import Message
from utils.sendMessage import SendMessage
from utils.str_utils import str_to_slug
from utils.misc_utils import stars, rank_text, pluriel
from utils.logger import Logger
from config import DB_PATH

class Pet(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'pet'), None)
    self.error_msg = Message(bot).message('error')
    self.help_msg = Message(bot).help('pet')
    self.command_service = CommandService()
    CommandService.init_command(self.pet_app_command, self.command)
    self.choices = CommandService.set_choices(Pet.get_pets())

  async def pet_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await self.command_service.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(pet=pet_autocomplete)
  @app_commands.command(name='pet')
  async def pet_app_command(self, interaction: discord.Interaction, pet: str):
    Logger.command_log('pet', interaction)
    await self.send_message.post(interaction)
    response = Pet.get_response(self, pet)
    await self.send_message.update(interaction, response)
    Logger.ok_log('pet')

  def get_response(self, pet):
    if str_to_slug(pet) == 'help':
      return self.help_msg
    pet_item = Pet.get_pet(pet)
    if not 'error' in pet_item.keys():
      response = {'title': '', 'description': Pet.description(self, pet_item), 'color': pet_item['color'], 'pic': pet_item['image_url']}
    else:
      description = f"{self.error_msg['description']['pet'][0]['text']} {pet} {self.error_msg['description']['pet'][1]['text']}"
      response = {'title': self.error_msg['title'], 'description': description, 'color': self.error_msg['color'], 'pic': None}
    return response
  
  def get_pets():
    pets = requests.get(f'{DB_PATH}pet').json()
    return [{'name': p['name'], 'name_slug': p['name_slug']} for p in pets]

  def get_pet(whichone):
    pet = requests.get(f'{DB_PATH}pet/{str_to_slug(whichone)}')
    return pet.json()
  
  def get_heroes_by_pet(pet_name):
    heroes = requests.get(f'{DB_PATH}hero/pet?pet={str_to_slug(pet_name)}')
    return heroes.json()
  
  def get_talent(whichone):
    talent = requests.get(f'{DB_PATH}talent/{str_to_slug(whichone)}')
    return talent.json()
   
  def description(self, pet):
    return Pet.print_header(pet) + Pet.print_stats(pet) + Pet.print_signature(pet) + Pet.print_full_talent(pet) + Pet.print_talents(pet) + Pet.print_comments(pet, Message(self.bot))
  
  def print_header(pet):
    return f"# {pet['name']}   {stars(pet['stars'])} #\n{pet['color']} pet pour {str.lower(pet['petclass'])}\n"
  
  def print_stats(pet):
    to_return = '### Attributs max : ###\n'
    to_return += f"+ {pet['attack']}% attaque/défense\n"
    return to_return
  
  def print_signature(pet):
    to_return = '### Héros signature : ###\n'
    to_return += pet['signature']
    if pet['signature_bis'] is not None:
      to_return += f" | {pet['signature_bis']}"
    to_return += '\n'
    return to_return
  
  def print_full_talent(pet):
    heroes = Pet.get_heroes_by_pet(pet['name'])
    if heroes:
      heroes = [h['name'] for h in heroes if h['name'] != pet['signature']]
      if len(heroes) > 0:
        pl = pluriel(heroes)
        to_return = f"### Autre{pl} héros pouvant bénéficier du full talent : ###\n"
        to_return += f"{', '.join(heroes)}\n"
        return to_return
    return ''
  
  def print_talents(pet):
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

    talent = Pet.get_talent(gold_talent['name'])
    to_return += f"-> {talent['description']}\n"
    to_return += f"__**Mana Cost :**__\n25 (base) - {25 - pet['manacost'] - manacost_merge} (gold) - {manacost_merge} (merge) = **{pet['manacost']}**\n"
    return to_return

  def print_comments(pet, message):
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

async def setup(bot):
  await bot.add_cog(Pet(bot))