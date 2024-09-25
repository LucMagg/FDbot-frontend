import discord
from discord.ext import commands
from discord import app_commands
import requests
from datetime import datetime
import typing

from utils.message import Message
from utils.sendMessage import SendMessage
from utils.str_utils import str_to_slug
from utils.misc_utils import stars, rank_text, pluriel
from service.command import CommandService

from utils.logger import Logger
from config import DB_PATH


class Hero(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'hero'), None)
    self.error_msg = Message(bot).message('error')
    self.help_msg = Message(bot).help('hero')
  
    self.command_service = CommandService()
    CommandService.init_command(self.hero_app_command, self.command)
    self.choices = CommandService.set_choices(Hero.get_heroes())

  async def héros_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await self.command_service.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(héros=héros_autocomplete)
  @app_commands.command(name='hero')
  async def hero_app_command(self, interaction: discord.Interaction, héros: str):
    Logger.command_log('hero', interaction)
    await self.send_message.post(interaction)
    response = Hero.get_response(self, héros)
    await self.send_message.update(interaction, response)
    Logger.ok_log('hero')

  def get_heroes():
    heroes = requests.get(f'{DB_PATH}hero').json()
    return [{'name': h['name'], 'name_slug': h['name_slug']} for h in heroes]

  def get_hero(whichone):
    hero = requests.get(f'{DB_PATH}hero/{str_to_slug(whichone)}')
    return hero.json()
  
  def get_pet(whichone):
    pet = requests.get(f'{DB_PATH}pet/{str_to_slug(whichone)}')
    return pet.json()
  
  def get_talent(whichone):
    talent = requests.get(f'{DB_PATH}talent/{str_to_slug(whichone)}')
    return talent.json()
  
  def get_response(self, héros):
    if str_to_slug(héros) == 'help':
      return self.help_msg
    hero = Hero.get_hero(héros)
    if not 'error' in hero.keys():
      if hero['pet'] is not None:
        pet = Hero.get_pet(hero['pet'])
      else:
        pet = None
      response = {'title': '', 'description': Hero.description(self, hero, pet), 'color': hero['color'], 'pic': hero['image_url']}
    else:
      description = f"{self.error_msg['description']['hero'][0]['text']} {héros} {self.error_msg['description']['hero'][1]['text']}"
      response = {'title': self.error_msg['title'], 'description': description, 'color': self.error_msg['color'], 'pic': None}
    return response
  
  def description(self, hero, pet):
    return Hero.print_header(hero) + Hero.print_stats(hero) + Hero.print_lead(hero) + Hero.print_talents(hero) + Hero.print_gear(hero, self.bot.static_data.qualities) + Hero.print_pet(hero, pet) + Hero.print_comments(hero, Message(self.bot).message('nocomment'))
  
  def print_header(hero):	
    return f"# {hero['name']}   {stars(hero['stars'])} #\n{hero['color']} {str.lower(hero['species'])} {str.lower(hero['heroclass'])}\n"

  def print_stats(hero):
    to_return = f"### Attributs max (A{hero['ascend']} - lvl {hero['lvl_max']}) : ###\n"
    to_return += '__**Attaque**__ : \n'
    to_return += f"**Total : {hero['att_max']}**\n"
    to_return += f"(base : {hero['attack']['max']} + équipements : {hero['att_gear']} + merge : {hero['att_merge']}"
    if hero['att_pet_boost'] != 0:
      to_return += f" + pet bonus : {hero['att_pet_boost']}"
    to_return +=  ')\n'
    to_return += f"{hero['att_rank']}{rank_text(hero['att_rank'])} sur {hero['class_count']} {str.lower(hero['heroclass'])}s (moyenne de la classe : {hero['att_average']})\n\n"

    to_return += '__**Défense**__ : \n'
    to_return += f"**Total : {hero['def_max']}**\n"
    to_return += f"(base : {hero['defense']['max']} + équipements : {hero['def_gear']} + merge : {hero['def_merge']}"
    if hero['def_pet_boost'] != 0:
      to_return += f" + pet bonus : {hero['def_pet_boost']}"
    to_return +=  ')\n'
    to_return += f"{hero['def_rank']}{rank_text(hero['def_rank'])} sur {hero['class_count']} {str.lower(hero['heroclass'])}s (moyenne de la classe : {hero['def_average']})\n\n"
    to_return += f"**Orientation offensive :** {round(hero['att_max']/hero['def_max']*100)}%\n"    
    
    return to_return

  def print_lead(hero):
    to_return = '### Bonus de lead : ###\n'
    for l in ['lead_color', 'lead_species']:
      lead = hero[l]

      print_lead = ''
      if lead['attack'] is not None:
        if lead['defense'] is not None:
          if lead['attack'] == lead['defense']:
            print_lead = f"{lead['attack']:.2f} att/def"
          else:
            print_lead = f"{lead['attack']:.2f} att and {lead['defense']:.2f} def"
        else:
          print_lead = f"{lead['attack']:.2f} att"
      else:
        if lead['defense'] is not None:
          print_lead = f"{lead['defense']:.2f} def"
        if lead['talent'] is not None:
          print_lead = lead['talent']
      
      if print_lead != '':
        print_lead += ' for '
        if lead['color'] is not None:
          print_lead += f"{str.lower(lead['color'])} "
        if lead['species'] is not None:
          print_lead += f"{str.lower(lead['species'])} "
        print_lead += 'heroes'
        to_return += f"{print_lead}\n"

    return to_return

  def print_talents(hero):
    base_talents = []
    ascend_talents = []
    merge_talents = []
    for i in range(1, 7):
      for t in hero['talents']:
        pos = t['position'].split(' ')
        if int(pos[1]) == i:
          match pos[0]:
            case 'base':
              base_talents.append(t['name'])
            case 'ascend':
              ascend_talents.append(t['name'])
            case 'merge':
              merge_talents.append(t['name'])

    to_return = '### Talents : ###\n'
    to_return += f"__**Base :**__\n{' | '.join([b for b in base_talents if b])}\n"
    to_return += f"__**Ascension :**__\n{' | '.join([a for a in ascend_talents if a])}\n"
    if len(merge_talents) > 0:
      to_return += f"__**Merge :**__\n{' __**ou**__ '.join([m for m in merge_talents if m])}\n"
    if len(hero['unique_talents']) > 0:
      pl = pluriel(hero['unique_talents'])
      to_return += f"\n__Talent{pl} unique{pl} pour un {str.lower(hero['heroclass'])} :__\n"
      to_return += f"{', '.join(h for h in hero['unique_talents'] if h)}\n"
    return to_return

  def print_gear(hero, qualities):
    to_return = '### Équipements : ###\n'
    for item in [{'to_find': 'A0', 'text': 'Base'}, 
                          {'to_find' : 'A1', 'text': '1ère ascension '},
                          {'to_find' : 'A2', 'text': '2ème ascension '},
                          {'to_find' : 'A3', 'text': '3ème ascension '}]:
      to_find = item['to_find']
      text = item['text']
      to_return += f"__**{text} :**__ (coût : " 

      price = 0
      gear_text = ''
      for pos in ['Amulet', 'Weapon', 'Ring', 'Head', 'Off-Hand', 'Body']:
        gear = next((g for g in hero['gear'] if g['ascend'] == to_find and g['position'] == pos), None)
        if gear:
          quality = next((q for q in qualities if q['name'] == gear['quality']), None)
          if quality:
            gear_text += f"{quality['icon']} {gear['quality']} {gear['name']}\n"
            price += quality['price']

      to_return += f"{price} :gem:)\n{gear_text}\n"
    return to_return
  
  def print_pet(hero, pet):
    if pet is not None:
      to_return = f"### Pet signature : {pet['name']} ###\n"
      to_return += f"Bonus max d'attaque/défense : {pet['attack']}%\n"

      full_talent = next((t for t in pet['talents'] if t['position'] == 'full'), None)
      to_return += f"Talent pour tous les {str.lower(hero['heroclass'])}s : {full_talent['name']}\n"

      gold_talent = next((t for t in pet['talents'] if t['position'] == 'gold'), None)
      to_return += f"Talent gold seulement pour {hero['name']} : {gold_talent['name']}\n"

      talent = Hero.get_talent(gold_talent['name'])
      if talent:
        to_return += f"-> {talent['description']} \n"
      return to_return
    else:
      return ''

  def print_comments(hero, nocomment):
    to_return = f"### Commentaire{pluriel(hero['comments'])} : ###\n"
    if len(hero['comments']) > 0:
      for comment in hero['comments']:
        my_date = datetime.strptime(comment['date'], "%a, %d %b %Y %H:%M:%S %Z").strftime("%d/%m/%Y")
        to_return += f"__{comment['author']} le {my_date}__\n"
        to_return += f"{comment['commentaire']}\n"
    else :
      to_return += nocomment['description']
    return to_return
      
    
async def setup(bot):
  await bot.add_cog(Hero(bot))