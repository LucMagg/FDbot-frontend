import discord
from discord.ext import commands
from discord import app_commands
import typing

from service.command import CommandService
from utils.message import Message
from utils.sendMessage import SendMessage
from utils.str_utils import slug_to_str, str_to_slug
from utils.misc_utils import stars



class Item(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'item'), None)
    self.help_msg = Message(bot).help('item')
    self.qualities = bot.static_data.qualities
    self.dusts = bot.static_data.dusts
    self.command_service = CommandService()
    CommandService.init_command(self.item_app_command, self.command)
    self.choices = None


  async def item_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await self.command_service.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(item=item_autocomplete)
  @app_commands.command(name='item')
  async def item_app_command(self, interaction: discord.Interaction, item: str):
    self.logger.command_log('item', interaction)
    self.logger.log_only('debug', f"arg : {item}")
    await self.send_message.post(interaction)
    response = await self.get_response(item, interaction)
    if response:
      await self.send_message.update(interaction, response)
    self.logger.ok_log('item')

  async def get_response(self, item, interaction):
    if str_to_slug(item) == 'help':
      return self.help_msg
    
    heroes = await self.get_heroes_by_item(item, interaction)
    if not heroes:
      return
    
    return{'title': '', 'description': self.description(item, heroes), 'color': 'default'}
  
  async def get_heroes_by_item(self, whichone, interaction):
    extract_quality = slug_to_str(whichone.split(' ')[0])
    quality = next((q for q in self.qualities if q['name'] == extract_quality), None)
    if quality:
      item = slug_to_str(' '.join(whichone.split(' ')[1:]))
      heroes = await self.bot.back_requests.call('getHeroesByGearNameAndQuality', True, [quality.get('name'), item], interaction)
    else:
      heroes = heroes = await self.bot.back_requests.call('getHeroesByGearName', True, [whichone], interaction)
    if heroes:
      return [heroes, quality]
    return
  
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

    if quality.get('discount_price') is None:
      discount_price = ''
    else:
      discount_price = f" ({quality['discount_price']}:gem: en promo)"
    to_return = '### Achat en boutique : ###\n'
    to_return += f"{quality['price']}:gem:{discount_price}\n"
    to_return += '### Recyclage : ###\n'
    to_return += f"* :moneybag: {quality['recycling']['gold']}\n"
    to_return += f"* {dust['icon']} {quality['recycling']['dust']['quantity']} {quality['recycling']['dust']['name']} dusts"
    return to_return
  
  async def setup(self, param_list):
    if param_list is None:
      choices = await self.bot.back_requests.call('getAllExistingGear', False)
    else:
      choices = param_list
    self.choices = CommandService.set_choices([{"name": c} for c in choices]) 


async def setup(bot):
  await bot.add_cog(Item(bot))