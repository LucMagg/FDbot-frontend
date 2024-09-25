import discord
from discord.ext import commands
from discord import app_commands
import requests
import typing

from service.command import CommandService
from utils.message import Message
from utils.sendMessage import SendMessage
from utils.str_utils import slug_to_str, str_to_slug
from utils.misc_utils import stars

from utils.logger import Logger
from config import DB_PATH


class Item(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'item'), None)
    self.error_msg = Message(bot).message('error')
    self.help_msg = Message(bot).help('item')
    self.qualities = bot.static_data.qualities
    self.dusts = bot.static_data.dusts
    self.command_service = CommandService()
    CommandService.init_command(self.item_app_command, self.command)
    self.choices = CommandService.set_choices(Item.get_items())


  async def item_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await self.command_service.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(item=item_autocomplete)
  @app_commands.command(name='item')
  async def item_app_command(self, interaction: discord.Interaction, item: str):
    Logger.command_log('item', interaction)
    await self.send_message.post(interaction)
    response = Item.get_response(self, item)
    await self.send_message.update(interaction, response)
    Logger.ok_log('item')

  def get_response(self, item):
    if str_to_slug(item) == 'help':
      return self.help_msg
    heroes = Item.get_heroes_by_item(self, item)
    if isinstance(heroes[0], list):
      response = {'title': '', 'description': Item.description(self, item, heroes), 'color': 'default', 'pic': None}
    else:
      description = f"{self.error_msg['description']['item'][0]['text']} {item} {self.error_msg['description']['item'][1]['text']}"
      response = {'title': self.error_msg['title'], 'description': description, 'color': self.error_msg['color'], 'pic': None}
    return response
  
  def get_heroes_by_item(self, whichone):
    quality = next((q for q in self.qualities if q['name'] == slug_to_str(whichone.split(' ')[0])), None)
    if quality:
      item = slug_to_str(' '.join(whichone.split(' ')[1:]))
      heroes = requests.get(f"{DB_PATH}hero/gear?gear_name={item}&gear_quality={quality['name']}")
    else:
      heroes = requests.get(f'{DB_PATH}hero/gear?gear_name={slug_to_str(whichone)}')
    return [heroes.json(), quality]
  
  def description(self, item, heroes):
    to_return = Item.print_header(item) + Item.print_sorted_list(item, heroes[0])
    if heroes[1] is not None:
      to_return += Item.print_quality(heroes[1], self.dusts)
    return to_return
  
  def print_header(item):
    return f"# {slug_to_str(item)} #\n"

  def print_sorted_list(item, list):
    list = sorted(list, key = lambda l: (l['stars'], l['name']))
    to_return = f"### Héros pouvant équiper {slug_to_str(item)} :###\n"

    star = 0
    for l in list:
      if star != l['stars']:
        star = l['stars']
        to_return += f"### {stars(l['stars'])} ###\n"
      multiple_items = ''
      if len(l['gear']) > 1:
        multiple_items = f"x{len(l['gear'])}"
      if isinstance(l['gear'][0], dict):
        format_gear = []
        for item in l['gear']:
          format_item = f"{item['ascend']} ({item['quality']})"
          format_gear.append(format_item)
        gear = ', '.join(format_gear)
      else:
        gear = ', '.join(l['gear'])
      to_return += f"{l['name']} ({l['color']} {str.lower(l['heroclass'])}) {multiple_items} : {gear}\n"
    return to_return
  
  def print_quality(quality, dusts):
    dust = next((d for d in dusts if d['name'] == quality['recycling']['dust']['name']), None)

    to_return = '### Achat en boutique : ###\n'
    to_return += f"{quality['price']}:gem: ({quality['discount_price']}:gem: en promo)\n"
    to_return += '### Recyclage : ###\n'
    to_return += f"* :moneybag: {quality['recycling']['gold']}\n"
    to_return += f"* {dust['icon']} {quality['recycling']['dust']['quantity']} {quality['recycling']['dust']['name']} dusts"
    return to_return
  
  def get_items():
    gear = requests.get(f"{DB_PATH}gear/all").json()
    return [{"name": g} for g in gear]
  

async def setup(bot):
  await bot.add_cog(Item(bot))