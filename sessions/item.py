from math import ceil

from ui.base_ui import BaseUiData
from states.item import ItemState

from utils.str_utils import slug_to_str, str_to_slug
from utils.misc_utils import stars

class ItemSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = ItemState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('item').get(self.ui.langcode)
    self.qualities = self.bot.static_data.qualities
    self.dusts = self.bot.static_data.dusts
    
    self.state.item = cog_data.get('item')

  # Session entry point
  async def start(self):
    try:
      self.ui.wait_message = True
      await self.ui.send()
      await self.ui.clear()
      self.ui.response = await self._get_response()
      await self.ui.send()
    except Exception as e:
      self.logger.session_exception('Item', e)

  # Get command response
  async def _get_response(self) -> dict:
    if str_to_slug(self.state.item) == self._translate('help'):
      return self.bot.message.get_help(whichone='item', lang=self.ui.langcode)
    self.state.parsed_item = self._parse_item_to_gear_and_quality()
    self.state.heroes = await self._get_heroes_by_item()
    if 'error' in self.state.heroes:
      return self._return_error(error='not found')
    self.state.levels = await self._get_drops_in_levels()
    return {'description': self._build_description(), 'color': 'default'}
  
  # Error builder
  def _return_error(self, error: str) -> dict:
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'not found':
        self.logger.log('debug', f'[ITEM] Item not found in DB : {self.state.item}')
        description += f'{self.error_msg.get('part1')}{self.state.item}{self.error_msg.get('part2')}'
      case 'request error':
        self.logger.log('error', f'[ITEM] Error while requesting backend')
        description += self.error_msg.get('generic')
    return {'description': description, 'color': self.bot.message.get_message('error').get('color')}
  
  # Description builder
  def _build_description(self) -> str:
    return (
      f'{self._display_header()}{self._display_sorted_list()}'
      f'{self._display_drop_levels() if self.state.levels else ''}'
      f'{self._display_quality() if self.state.parsed_item.get('quality') else ''}'
    )
  
  # Item parser to {'item', 'quality'} 
  def _parse_item_to_gear_and_quality(self) -> dict:
    extract_quality = str_to_slug(self.state.item.split(' ')[0])
    quality = next((q for q in self.qualities if q.get('name_slug') == extract_quality), None)
    return {'item': slug_to_str(' '.join(self.state.item.split(' ')[1:])) if quality else self.state.item, 'quality': quality}
  
  # Get matching heroes
  async def _get_heroes_by_item(self) -> dict|None:
    if self.state.parsed_item.get('quality'):
      request = 'getHeroesByGearNameAndQuality'
      args = [self.state.parsed_item.get('quality').get('name').get('en'), self.state.parsed_item.get('item')]
    else:
      request = 'getHeroesByGearName'
      args = [self.state.parsed_item.get('item')]
    heroes = await self.bot.back_requests.call(request, args)
    if 'error' in heroes:
      return None
    return heroes
  
  # Get matching levels
  async def _get_drops_in_levels(self) -> dict|None:
    json_param = {'item': self.state.parsed_item.get('item')}
    if self.state.parsed_item.get('quality'):
      json_param['quality'] = self.state.parsed_item.get('quality').get('name').get('en')
    json_param['lang'] = 'en'
    levels = await self.bot.back_requests.call('getLevelsByGear', [json_param])
    if 'error' in levels:
      return None
    return levels    
  
  # Description helpers
  #    Header
  def _display_header(self) -> str:
    if self.state.parsed_item.get('quality'):
      to_translate = f'{slug_to_str(self.state.parsed_item.get('quality').get('name_slug'))} {slug_to_str(self.state.parsed_item.get('item'))}'
    else:
      to_translate = slug_to_str(self.state.parsed_item.get('item'))
    return f'# {self._translate(to_translate)} #\n'

  #    Sorted list of heroes
  def _display_sorted_list(self) -> str:
    list = sorted(self.state.heroes, key = lambda h: (h.get('stars'), h.get('name')))
    result = f'### {self.return_msg.get('heroes')} : ###\n'
    star = 0
    for l in list:
      if star != l.get('stars'):
        star = l.get('stars')
        result += f'### {stars(l.get('stars'))} ###\n'
      multiple_items = ''
      if len(l.get('gear')) > 1:
        multiple_items = f' x{len(l.get('gear'))}'
      if isinstance(l.get('gear')[0], dict):
        format_gear = []
        for i in l.get('gear'):
          format_gear.append(f'{i.get('ascend')} ({self._translate(i.get('quality'))})')
        gear = ', '.join(format_gear)
      else:
        gear = ', '.join([self._translate(g) for g in l.get('gear')])
      result += f'{self._translate(l.get('name'))} ({self._translate(f'{l.get('color')} {l.get('heroclass')}')}) {multiple_items} : {gear}\n'
    return result
  
  #    Drop levels
  def _display_drop_levels(self) -> str:
    header = f'### {self.return_msg.get('where')} : ###\n'
    lines = []
    for level in self.state.levels:
      level_name = level.get('name').get(self.ui.langcode) or level.get('name').get('en')
      loot, loot_type = self._calculate_loot(level)
      line = f'- {level_name}'
      if loot:
          line += f' : {self.return_msg.get('proba')} {loot} ({loot_type})'
      lines.append(line)
    return header + '\n'.join(lines) + '\n'
  
  #    Quality
  def _display_quality(self) -> str:
    quality = self.state.parsed_item.get('quality')
    dust = next((d for d in self.dusts if d.get('name') == quality.get('recycling').get('dust').get('name')), None)
    if not quality.get('discount_price'):
      discount_price = ''
    else:
      discount_price = f' ({self.return_msg.get('discount')} {quality.get('discount_price')}:gem:)'
    result = (
      f'### {self.return_msg.get('buy')} : ###\n'
      f'{quality.get('price')}:gem:{discount_price}\n'
      f'### {self.return_msg.get('recycle')} : ###\n'
      f'* :moneybag: {quality.get('recycling').get('gold')}\n'
    )
    if dust:
      result += (
        f'* {dust.get('icon')} {quality.get('recycling').get('dust').get('quantity')} '
        f'{quality.get('recycling').get('dust').get('name').get(self.ui.langcode).lower()}'
      )
    return result
  
  # Loot helpers
  def _get_item_loot(self, level: dict, total_appearances: int, quality_name: str = None) -> tuple:
    gear_reward = next((r for r in level.get('reward_choices', []) if r.get('name') == 'gear'), {})
    item_choices = next((c.get('choices', []) for c in gear_reward.get('choices', []) if c.get('name') == 'Item'), [])
    item_count = len(item_choices)
    if quality_name:
      items_appearances = sum(r.get('total_appearances', 0) for r in level.get('rewards', []) if r.get('type') == 'gear' and r.get('quality') == quality_name)
    else:
      items_appearances = sum(r.get('total_appearances', 0) for r in level.get('rewards', []) if r.get('type') == 'gear')
    if items_appearances == 0:
      return 0, self.return_msg.get('calculated')
    if len(level.get('reward_choices', [])) == 1:
      return item_count, self.return_msg.get('calculated')
    return ceil(total_appearances / (items_appearances or 1) * item_count), self.return_msg.get('calculated')

  def _calculate_loot(self, level: dict) -> tuple:
    total_appearances = sum(r.get('total_appearances', 0) for r in level.get('rewards', []))
    if total_appearances < 50:
      return None, None
    item_name = self.state.parsed_item.get('item')
    has_quality = bool(self.state.parsed_item.get('quality'))
    if has_quality:
      quality_name = self.state.parsed_item.get('quality').get('name', {}).get('en')
      found_quality = next((r for r in level.get('rewards', []) if r.get('type') == 'gear' and r.get('quality') == quality_name), None)
      found_item = next((d for d in found_quality.get('details', []) if d.get('item') == item_name), None) if found_quality else None
      if found_item and total_appearances > 100:
        appearances = found_item.get('appearances') or 1
        return ceil(total_appearances / appearances), self.return_msg.get('real')
      if found_quality:
        return self._get_item_loot(level, total_appearances, quality_name)
      return None, None
    found_items = [d for r in level.get('rewards', []) if r.get('type') == 'gear' for d in r.get('details', []) if d.get('item') == item_name]
    if found_items and total_appearances > 100:
      total_found_appearances = sum(f.get('appearances', 1) for f in found_items)
      if total_found_appearances == 0:
        total_found_appearances = 1
      return ceil(total_appearances / total_found_appearances), self.return_msg.get('real')
    return self._get_item_loot(level, total_appearances)
  
  # Translate helper
  def _translate(self, key) -> str:
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)