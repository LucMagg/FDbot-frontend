import discord
from discord.ext import commands
from discord import app_commands
import typing
from math import ceil

from service.command import CommandService
from utils.message import Message
from service.interaction_handler import InteractionHandler
from utils.str_utils import slug_to_str, str_to_slug, format_float
from utils.misc_utils import stars

str_gap = '\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0'

class Item(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.interaction_handler = InteractionHandler(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'item'), None)
    self.help_msg = Message(bot).help('item')
    self.qualities = bot.static_data.qualities
    self.dusts = bot.static_data.dusts
    
    CommandService.init_command(self.item_app_command, self.command)
    self.choices = None

  async def item_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await CommandService.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(item=item_autocomplete)
  @app_commands.command(name='item')
  async def item_app_command(self, interaction: discord.Interaction, item: str):
    self.logger.command_log('item', interaction)
    self.logger.log_only('debug', f"arg : {item}")
    await self.interaction_handler.handle_response(interaction=interaction, wait_msg=True)
    response = await self.get_response(item, interaction)
    if response:
      await self.interaction_handler.handle_response(interaction=interaction, response=response)
    self.logger.ok_log('item')

  async def get_response(self, item, interaction):
    if str_to_slug(item) == 'help':
      return self.help_msg
    item = self.parse_item_to_gear_and_quality(item)
    heroes = await self.get_heroes_by_item(item, interaction)
    if not heroes:
      return
    levels = await self.get_drops_in_levels(item)
    return {'title': '', 'description': self.description(item, heroes, levels), 'color': 'default'}
  
  def parse_item_to_gear_and_quality(self, item):
    extract_quality = slug_to_str(item.split(' ')[0]).capitalize()
    quality = next((q for q in self.qualities if q.get('name') == extract_quality), None)
    return {'item': slug_to_str(' '.join(item.split(' ')[1:])) if quality else item, 'quality': quality}
  
  async def get_heroes_by_item(self, item, interaction):
    if item.get('quality') is None:
      heroes = await self.bot.back_requests.call('getHeroesByGearName', True, [item.get('item')], interaction)
    else:
      heroes = await self.bot.back_requests.call('getHeroesByGearNameAndQuality', True, [item.get('quality').get('name'), item.get('item')], interaction)
    if heroes:
      return heroes
    return None
  
  async def get_drops_in_levels(self, item):
    json_param = {'item': item.get('item')}
    if item.get('quality') is not None:
      json_param['quality'] = item.get('quality').get('name')
    print(json_param)
    levels = await self.bot.back_requests.call('getLevelsByGear', False, [json_param])
    if levels:
      return levels
    return None
  
  def description(self, item, heroes, levels) -> str:
    to_return = self.print_header(item) + self.print_sorted_list(heroes)
    if levels is not None:
      to_return += self.print_drop_levels(item, levels)
    if item.get('quality') is not None:
      to_return += self.print_quality(item.get('quality'))
    return to_return
  
  def print_header(self, item) -> str:
    to_return = '#'
    if item.get('quality') is not None:
      to_return += f' {item.get('quality').get('name')}'
    to_return += f' {slug_to_str(item.get('item'))} #\n'
    return to_return

  def print_sorted_list(self, list) -> str:
    list = sorted(list, key = lambda l: (l.get('stars'), l.get('name')))
    to_return = '### Héros pouvant équiper cet objet :###\n'

    star = 0
    for l in list:
      if star != l.get('stars'):
        star = l.get('stars')
        to_return += f'### {stars(l.get('stars'))} ###\n'
      multiple_items = ''
      if len(l.get('gear')) > 1:
        multiple_items = f"x{len(l.get('gear'))}"
      if isinstance(l.get('gear')[0], dict):
        format_gear = []
        for i in l.get('gear'):
          format_item = f'{i.get('ascend')} ({i.get('quality')})'
          format_gear.append(format_item)
        gear = ', '.join(format_gear)
      else:
        gear = ', '.join(l.get('gear'))
      to_return += f"{l.get('name')} ({l.get('color')} {str.lower(l.get('heroclass'))}) {multiple_items} : {gear}\n"
    return to_return
  
  def print_drop_levels(self, item, levels) -> str:
    to_return = '### Où trouver cet objet :###\n'

    for level in levels:
      to_return += f'- {level.get('name')}'
      total_appearances = sum([r.get('total_appearances') for r in level.get('rewards')])
      found_quality = next((r for r in level.get('rewards') if r.get('type') == 'gear' and r.get('quality') == item.get('quality').get('name')), None)
      if found_quality:
        found_item = next((r for r in found_quality.get('details') if r.get('item') == item.get('item')), None)
        if found_item:
          loot = ceil(total_appearances / found_item.get('appearances'))
          to_return += f' : 1 chance sur {loot} (probabilité réelle)'
        else:
          gear_reward = next((r for r in level.get('reward_choices') if r.get('name') == 'gear'), None)
          item_reward_count = len(next((r.get('choices') for r in gear_reward.get('choices') if r.get('name') == 'Item'), None))
          loot = ceil(total_appearances / found_quality.get('total_appearances') * item_reward_count)
          to_return += f' : 1 chance sur {loot} (probabilité calculée)'
      to_return += '\n'
    return to_return

  def print_quality(self, quality) -> str:
    dust = next((d for d in self.dusts if d.get('name') == quality.get('recycling').get('dust').get('name')), None)
    if quality.get('discount_price') is None:
      discount_price = ''
    else:
      discount_price = f' ({quality.get('discount_price')}:gem: en promo)'
    to_return = '### Achat en boutique : ###\n'
    to_return += f'{quality.get('price')}:gem:{discount_price}\n'
    to_return += '### Recyclage : ###\n'
    to_return += f'* :moneybag: {quality.get('recycling').get('gold')}\n'
    if dust:
      to_return += f'* {dust.get('icon')} {quality.get('recycling').get('dust').get('quantity')} {quality.get('recycling').get('dust').get('name')} dusts'
    return to_return
  
  async def setup(self, param_list):
    if param_list is None:
      choices = await self.bot.back_requests.call('getAllExistingGear', False)
    else:
      choices = param_list
    self.choices = CommandService.set_choices([{'name': c} for c in choices]) 


async def setup(bot):
  await bot.add_cog(Item(bot))