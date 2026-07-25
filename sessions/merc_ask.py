from ui.base_ui import BaseUiData
from states.merc import MercState

from ui.merc.common import MercCommon

from utils.str_utils import str_to_slug
from utils.misc_utils import nick


class MercAskSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = MercState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('merc').get(self.ui.langcode)
    
    self.state.merc['name'] = cog_data.get('hero')
    self.state.user = nick(cog_data.get('interaction'))
    self.state.user_id = cog_data.get('interaction').user.id
    self.state.guild_id = cog_data.get('interaction').guild.id

  # Session entry point
  async def start(self):
    self.ui.wait_message = True
    await self.ui.send()
    await self.ui.clear()
    self.ui.response = await self._get_response()
    await self.ui.send()

  # Get command response
  async def _get_response(self) -> dict:
    if str_to_slug(self.state.user) == self._translate('help'):
      return self.bot.message.get_help(whichone='merc ask', lang=self.ui.langcode)
    self.state.found_hero = await self.bot.back_requests.call('getHeroByName', [str_to_slug(self.state.merc.get('name'))])
    if 'error' in self.state.found_hero:
      return self._return_error('hero not found')
    self.state.user_list = await self.bot.back_requests.call('getMerc', [{'name': self.state.found_hero.get('name'), 'guild_id': self.state.guild_id}])
    if not self.state.user_list or 'error' in self.state.user_list:
      return self._return_error('merc not found')
    self.state.user_list = [i for i in self.state.user_list if i.get('user_id') != self.state.user_id]
    if len(self.state.user_list) == 0:
      return self._return_error('no other merc')
    return {'description': self._build_description(), 'color': 'default'}
  
  # Error builder
  def _return_error(self, error: str) -> dict:
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'hero not found':
        self.logger.log_only('error', f'[MERC ASK] Hero not found : {self.state.merc.get('name')}')
        description += (
          f'{self.error_msg.get('merc').get('part1')}{self.state.merc.get('name')}'
          f'{self.error_msg.get('merc').get('not found')}{self.error_msg.get('merc').get('part2')}'
        )
      case 'merc not found':
        self.logger.log_only('debug', f'[MERC ASK] Merc not found : {self.state.found_hero.get('name')}')
        description += (
          f'{self.error_msg.get('merc').get('part1')}{self.state.found_hero.get('name')}'
          f'{self.error_msg.get('merc').get('no merc')}{self.error_msg.get('merc').get('part2')}'
        )
      case 'no other merc':
        self.logger.log_only('debug', f'[MERC ASK] No other player has merc : {self.state.found_hero.get('name')}')
        description += (
          f'{self.error_msg.get('merc').get('no other1')}{self.state.found_hero.get('name')}'
          f'{self.error_msg.get('merc').get('no other2')}'
        )
    return {'description': description, 'color': self.bot.message.get_message('error').get('color')}
  
  # Description builder
  def _build_description(self) -> str:
    return (
      f'## {self.state.user} {self.return_msg.get('needs')} {self.state.found_hero.get('name')} ##\n'
      f'{'\n'.join(self._display_users())}'
      f'\n{self.return_msg.get('thx')}\n'
    )
  
  # Display users helper
  def _display_users(self) -> list[str]:
    result = []
    for user in self.state.user_list:
      to_append = ''
      if len(self.state.user_list) > 1:
        to_append += '- '
      to_append += f'<@{user.get('user_id')}> {MercCommon.display_merc_details(user.get('merc'), self.return_msg)}'
      result.append(to_append)
    return result
  
  # Translate helper
  def _translate(self, key) -> str:
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)