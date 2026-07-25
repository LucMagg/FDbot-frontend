from ui.base_ui import BaseUiData
from states.talent import TalentState

from utils.str_utils import str_to_slug
from utils.misc_utils import stars

class TalentSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = TalentState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('talent').get(self.ui.langcode)
    
    self.state.talent = cog_data.get('talent')

  # Session entry point
  async def start(self):
    self.ui.wait_message = True
    await self.ui.send()
    await self.ui.clear()
    self.ui.response = await self._get_response()
    await self.ui.send()

  # Get command response
  async def _get_response(self) -> dict:
    if str_to_slug(self.state.talent) == self._translate('help'):
      return self.bot.message.get_help(whichone='talent', lang=self.ui.langcode)
    self.state.talent_dict = await self._get_talent()
    if 'error' in self.state.talent_dict:
      return self._return_error(error='not found')
    self.state.heroes = await self._get_heroes()
    self.state.pets = await self._get_pets()
    if 'error' in self.state.heroes and 'error' in self.state.pets:
      return self._return_error(error='no hero or pet')
    return {'description': self._build_description(), 'color': 'default'}
  
  # Error builder
  def _return_error(self, error: str) -> dict:
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'not found':
        self.logger.log_only('debug', f'[TALENT] Talent not found in DB : {self.state.talent}')
        description += f'{self.error_msg.get('talent').get('part1')}{self.state.talent}{self.error_msg.get('talent').get('part2')}'
      case 'no hero or pet':
        self.logger.log_only('error', f'[TALENT] No hero nor pet found in DB : {self.state.talent}')
        description += f'{self.error_msg.get('talent').get('no talent1')}{self.state.talent}{self.error_msg.get('talent').get('no talent2')}'
    return {'description': description, 'color': self.bot.message.get_message('error').get('color')}
  
  # Description builder
  def _build_description(self) -> str:
    return (
      self._display_header() +
      self._display_lists()
    )
    
  # Description helpers
  #    Header
  def _display_header(self):
    return (
      f'## {self.state.talent_dict.get('name')} ##\n'
      f'{self.state.talent_dict.get('description') if self.state.talent_dict.get('description') else ''}\n'
    )

  def _display_lists(self):
    result = ''
    for list, whichone in [(self.state.heroes, 'hero'), (self.state.pets, 'pet')]:
      if 'error' in list:
        continue
      list = sorted(list, key = lambda l: (l.get('stars'), l.get('name')))
      result += f'### {self.return_msg.get(whichone)} {self.state.talent_dict.get('name')} : ###\n'
      star = 0
      for l in list:
        if star != l.get('stars'):
          star = l.get('stars')
          result += f'### {stars(star)} ###\n'
        multiple_talents = ''
        if len(l.get('talents')) > 1:
          multiple_talents = f'x{len(l['talents'])}'
        talents = ', '.join(l.get('talents'))
        result += f'{self._translate(l.get('name'))} ({self._translate(f'{l.get('color')} {l.get(f'{whichone}class')}')}) {multiple_talents} : {talents}\n'
    return result
  
  # Request helpers
  #    talent
  async def _get_talent(self):
    return await self.bot.back_requests.call('getTalentByName', [self.state.talent])

  #    heroes
  async def _get_heroes(self):
    return await self.bot.back_requests.call('getHeroesByTalent', [self.state.talent_dict.get('name')])

  #    pets
  async def _get_pets(self):
    return await self.bot.back_requests.call('getPetsByTalent', [self.state.talent_dict.get('name')])

  # Translate helper
  def _translate(self, key):
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)