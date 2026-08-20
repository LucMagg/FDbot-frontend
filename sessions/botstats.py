from ui.base_ui import BaseUiData
from states.botstats import BotStatsState

from collections import Counter
from utils.misc_utils import stars

class BotStatsSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = BotStatsState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('botstats').get(self.ui.langcode)

  # Session entry point
  async def start(self):
    try:
      self.ui.wait_message = True
      await self.ui.send()
      await self.ui.clear()
      self.ui.response = await self._get_response()
      await self.ui.send()
    except Exception as e:
      self.logger.session_exception('BotStats', e)

  # Get command response
  async def _get_response(self) -> dict:
    self.state.talents = await self.bot.back_requests.call('getAllTalents')
    if not self.state.talents:
      return self._return_error()
    self.state.heroes = await self.bot.back_requests.call('getAllHeroes')
    if not self.state.heroes:
      return self._return_error()
    self.state.pets = await self.bot.back_requests.call('getAllPets')
    if not self.state.pets:
      return self._return_error()
    return {'description': self._build_description(), 'color': self.bot.message.get_message('botstats').get('color')}
  
  # Error builder
  def _return_error(self) -> dict:
    self.logger.log('error', f'[ADDREPLAY] Error while requesting backend')
    description = f'## {self.error_msg.get('title')} ##\n{self.error_msg.get('generic')}'
    return {'description': description, 'color': self.bot.message.get_message('error').get('color')}

  # Description builder
  def _build_description(self) -> str:
    description = (
      f'## {self.return_msg.get('title')} ##\n'
      f'### {len(self.state.heroes)} {self.return_msg.get('heroes')} ###\n'
      f'* {self._detailed_count(self.state.heroes, 'heroclass')}\n'
      f'### {len(self.state.pets)} {self.return_msg.get('pets')} ###\n'
      f'* {self._detailed_count(self.state.pets, 'petclass')}\n'
      f'### {len(self.state.talents)} {self.return_msg.get('talents')} ###\n'
    )
    return description

  # Helpers
  #    Count dispatcher
  def _detailed_count(self, list: list, whichone: str) -> str:
    detailed_count = f'{self._count_stars(list)}{self._count_attribute(list, attribute='color', text_message='colors')}'
    if whichone == 'heroclass':
      detailed_count += self._count_attribute(list, attribute='species', text_message='species')
    detailed_count += self._count_attribute(list, attribute=whichone, text_message='classes')
    return detailed_count

  #    Stars counter
  def _count_stars(self, list: list) -> str:
    list_stars_count = Counter(l['stars'] for l in list)
    l_stars_print = []
    for k, v in sorted(list_stars_count.items()):
      l_stars_print.append(f'{v} {stars(k)}')
    return f'{', '.join(l_stars_print)}\n'
  
  #    Generic attribute counter
  def _count_attribute(self, list: list, attribute: str, text_message: str) -> str:
    list_attribute_count = Counter(l[attribute] for l in list)
    list_attribute_print = []
    for k, v in sorted(list_attribute_count.items()):
      translated = self._translate(f'{k} {'S' if v == 1 else 'P'}')
      list_attribute_print.append((translated, v))
    list_attribute_print.sort(key=lambda x: x[0])
    return f'* {len(list_attribute_count)} {self.return_msg.get(text_message)} {', '.join(f'{v} {name}' for name, v in list_attribute_print)}\n'
  
  #    Translate
  def _translate(self, key) -> str:
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)