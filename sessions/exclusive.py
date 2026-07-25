from collections import defaultdict

from ui.base_ui import BaseUiData
from states.exclusive import ExclusiveState

from utils.str_utils import str_to_slug

class ExclusiveSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = ExclusiveState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('exclusive').get(self.ui.langcode)

    self.state.event = cog_data.get('event')
    self.mapping = {'heroes': {'class_key': 'heroclass', 'has_species': True}, 'pets': {'class_key': 'petclass', 'has_species': False}}

  # Session entry point
  async def start(self):
    self.ui.wait_message = True
    await self.ui.send()
    await self.ui.clear()
    self.ui.response = await self._get_response()
    await self.ui.send()

  # Get command response
  async def _get_response(self) -> dict:
    if str_to_slug(self.state.event) == self._translate('help'):
      return self.bot.message.get_help(whichone='exclusive', lang=self.ui.langcode)
    if str_to_slug(self.state.event) == self._translate('all'):
      self.state.event = None
    self.state.heroes = await self.bot.back_requests.call('getExclusiveHeroes', [{'type': self.state.event}])
    if 'error' in self.state.heroes:
      return self._return_error()
    self.state.pets = await self.bot.back_requests.call('getExclusivePets', [{'type': self.state.event}])
    if 'error' in self.state.pets:
      self.state.pets = []
    self.state.exclusives = self._merge_lists()
    description = self._build_description()
    color = self.state.embed_color if self.state.embed_color else self.bot.message.get_message('exclusive').get('color')
    return {'title': '', 'description': description, 'color': color}
  
  # Error builder
  def _return_error(self) -> dict:
    self.logger.log_only('debug', f'[EXCLUSIVE] Event not found in DB : {self.state.event}')
    description = (
      f'## {self.error_msg.get('title')} ##\n' +
      f'{self.error_msg.get('exclusive').get('part1')}{self.state.event}{self.error_msg.get('exclusive').get('part2')}'
    )
    return {'description': description, 'color': self.bot.message.get_message('error').get('color')}
   
  # Description builder
  def _build_description(self) -> str:
    return self._display_header() + self._display_list()
  
  # Description helpers
  #    Header
  def _display_header(self) -> str:
    if self.state.event is None:
      return f'## {self.return_msg.get('title')} ##\n'
    return f' ## {self._translate(self.state.heroes[0].get('exclusive'))} ##\n'
  
  #    List
  def _display_list(self) -> str:
    result = ''
    for item in self.state.exclusives:
      if self.state.event is None:
        result += f'### {self._translate(item.get('exclusive'))}{self.return_msg.get('exclusives')} ###\n'
      for key, config in self.mapping.items():
        elements = item.get(key)
        if not elements:
          continue
        if key == 'pets':
          result += '\n'
        result += f'__** {self.return_msg.get(key)} **__\n'
        for i in elements:
          has_species = config.get('has_species')
          color, species = i.get('color'), i.get('species')
          if self.state.embed_color:
            mid = f' {self._translate(f'{species} S').lower()} ' if has_species else ''
          else:
            mid = f' {self._translate(f'{color} {species} S').lower()} ' if has_species else f' {self._translate(f'{color} S').lower()}'
          result += (
            f'{self._translate(i.get('name'))}'
            f' ({self._translate(f'{i.get(config.get('class_key'))} S')}'
            f'{mid} {i.get('stars')}:star:)\n'
          )
    return result
  
  #    Merge heroes & pets
  def _merge_lists(self) -> list[dict]:
    merged = defaultdict(lambda: {'heroes': [], 'pets': []})
    first_color = None
    same_color = True

    sources = [(self.state.heroes, 'heroes'), (self.state.pets, 'pets')]
    for source, key in sources:
      for item in source:
        elements = item.get(key, [])
        merged[item['exclusive']][key] = elements
        first_color, same_color = self._get_unique_color(elements, first_color, same_color)
    
    self.state.embed_color = first_color if same_color else None
    return [{'exclusive': k, **v} for k, v in merged.items()]

  #    Get unique color
  def _get_unique_color(self, elements: list[dict], first_color: str|None, same_color: bool) -> tuple[str|None, bool]:
    for el in elements:
      color = el.get('color')
      if not color:
        continue
      if first_color is None:
        first_color = color
      elif color != first_color:
        same_color = False
    return first_color, same_color
  
  # Translate helper
  def _translate(self, key):
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)