from ui.base_ui import BaseUiData
from states.classe import ClasseState

from utils.str_utils import str_to_slug
from utils.misc_utils import stars, rank_text


class ClasseSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = ClasseState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('class').get(self.ui.langcode)

    self.state.classe = cog_data.get('classe')

  # Session entry point  
  async def start(self):
    self.ui.wait_message = True
    await self.ui.send()
    await self.ui.clear()
    self.ui.response = await self._get_response()
    await self.ui.send()

  # Get command response
  async def _get_response(self) -> dict:
    if str_to_slug(self.state.classe) == self._translate('help'):
      class_list = '\n'.join([f'* {c.name}' for c in self.cog.choices[self.ui.langcode]])
      return self.bot.message.get_help(whichone='class', lang=self.ui.langcode, options=class_list)
    self.state.pets = await self.bot.back_requests.call('getPetsByClass', [self.state.classe])
    self.state.heroes = await self.bot.back_requests.call('getHeroesByClass', [self.state.classe])
    if 'error' in self.state.heroes:
      return self._return_error(error='request error')
    if 'error' in self.state.heroes and 'error' in self.state.pets:
      return self._return_error(error='not found')
    return {'description': self._build_description(), 'color': self.bot.message.get_message('class').get('color')}
  
  # Error builder
  def _return_error(self, error: str) -> dict:
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'not found':
        self.logger.log_only('debug', f'[CLASS] Argument not found in DB : {self.state.classe}')
        description += f'{self.error_msg.get('class').get('part1')}{self.state.classe}{self.error_msg.get('class').get('part2')}'
      case 'request error':
        self.logger.log_only('error', f'[CLASS] Error while requesting backend')
        description += self.error_msg.get('generic')
    return {'description': description, 'color': self.bot.message.get_message('error').get('color')}
  
  # Description builder
  def _build_description(self) -> str:
    description = f'## {self._translate(f'{self.state.classe} S')} ##\n'
    if isinstance(self.state.heroes, list):
      description += self.display_sorted_list('heroes', self.state.heroes)
    if isinstance(self.state.pets, list):
      description += self.display_sorted_list('pets', self.state.pets)
    return description
  
  # Sorted list builder
  def display_sorted_list(self, whichone: str, list: list) -> str:
    list = sorted(list, key = lambda l: (l.get('stars'), l.get('name')))
    result = f'### {self.return_msg.get(whichone)} ###\n'

    star = 0
    for l in list:
      if star != l.get('stars'):
        star = l.get('stars')
        result += f'### {stars(l['stars'])} ###\n'
      result += f'** {self._translate(l.get('name'))} **('

      match whichone:
        case 'heroes':
          att_rank = f'{l.get('att_rank')}{self._translate(rank_text(l.get('att_rank')))}'
          def_rank = f'{l.get('def_rank')}{self._translate(rank_text(l.get('def_rank')))}'
          result += (
            f'{self._translate(f'{l.get('color')} {l.get('species')} S')}) - '
            f'{self.return_msg.get('att')} {l.get('att_max')} ({att_rank}) | '
            f'{self.return_msg.get('def')} {l.get('def_max')} ({def_rank})\n'
          )
        case 'pets':
          result += (
            f'{self._translate(f'{l.get('color')} S')}) : '
            f'{self._translate(l.get('signature'))}'
          )
          result += f', {self._translate(l.get('signature_bis'))}\n' if l.get('signature_bis') else '\n'
    return result
  
  # Translate helper
  def _translate(self, key) -> str:
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)