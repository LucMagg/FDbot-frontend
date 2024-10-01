import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import typing

from utils.message import Message
from utils.sendMessage import SendMessage
from utils.str_utils import str_to_slug
from utils.misc_utils import stars, rank_text, pluriel
from service.command import CommandService


class Hero(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'hero'), None)
    self.help_msg = Message(bot).help('hero')
  
    self.command_service = CommandService()
    CommandService.init_command(self.hero_app_command, self.command)
    self.choices = None

  async def héros_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await self.command_service.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(héros=héros_autocomplete)
  @app_commands.command(name='hero')
  async def hero_app_command(self, interaction: discord.Interaction, héros: str):
    self.logger.command_log('hero', interaction)
    self.logger.log_only('debug', f"arg : {héros}")
    await self.send_message.post(interaction)
    response = await self.get_response(héros, interaction)
    await self.send_message.update(interaction, response)
    self.logger.ok_log('hero')
  
  async def get_response(self, héros, interaction):
    if str_to_slug(héros) == 'help':
      return self.help_msg
    
    hero = await self.bot.back_requests.call('getHeroByName', True, [héros], interaction)
    if not hero:
      return
    
    if hero['pet'] is not None:
      pet = await self.bot.back_requests.call('getPetByName', False, [hero.get('pet')], interaction)
    else:
      pet = False

    return {'title': '', 'description': await self.description(hero, pet), 'color': hero['color'], 'pic': hero['image_url']}
  
  async def description(self, hero, pet):
    return self.print_header(hero) + self.print_stats(hero) + self.print_lead(hero) + self.print_talents(hero) + self.print_gear(hero) + await self.print_pet(hero, pet) + self.print_comments(hero, Message(self.bot).message('nocomment'))
  
  def print_header(self, hero):	
    return f"# {hero['name']}   {stars(hero['stars'])} #\n{hero['color']} {str.lower(hero['species'])} {str.lower(hero['heroclass'])}\n"

  def print_stats(self, hero):
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

  def print_lead(self, hero):
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

  def print_talents(self, hero):
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

  def print_gear(self, hero):
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
          quality = next((q for q in self.bot.static_data.qualities if q['name'] == gear['quality']), None)
          if quality:
            gear_text += f"{quality['icon']} {gear['quality']} {gear['name']}\n"
            price += quality['price']

      to_return += f"{price} :gem:)\n{gear_text}\n"
    return to_return
  
  async def print_pet(self, hero, pet):
    if pet:
      to_return = f"### Pet signature : {pet['name']} ###\n"
      to_return += f"Bonus max d'attaque/défense : {pet['attack']}%\n"

      full_talent = next((t for t in pet['talents'] if t['position'] == 'full'), None)
      to_return += f"Talent pour tous les {str.lower(hero['heroclass'])}s : {full_talent['name']}\n"

      gold_talent = next((t for t in pet['talents'] if t['position'] == 'gold'), None)
      to_return += f"Talent gold seulement pour {hero['name']} : {gold_talent['name']}\n"

      talent = await self.bot.back_requests.call('getTalentByName', False, [gold_talent['name']])
      if talent:
        to_return += f"-> {talent['description']} \n"
      return to_return
    else:
      return ''

  def print_comments(self, hero, nocomment):
    to_return = f"### Commentaire{pluriel(hero['comments'])} : ###\n"
    if len(hero['comments']) > 0:
      for comment in hero['comments']:
        my_date = datetime.strptime(comment['date'], "%a, %d %b %Y %H:%M:%S %Z").strftime("%d/%m/%Y")
        to_return += f"__{comment['author']} le {my_date}__\n"
        to_return += f"{comment['commentaire']}\n"
    else :
      to_return += nocomment['description']
    return to_return
  
  async def setup(self):
    choices = await self.bot.back_requests.call('getAllHeroes', False)
    self.choices = CommandService.set_choices(choices) 
      
    
async def setup(bot):
  await bot.add_cog(Hero(bot))