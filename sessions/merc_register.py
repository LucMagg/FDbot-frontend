from ui.base_ui import BaseUiData
from states.merc import MercState

from ui.merc.common import MercCommon

from utils.str_utils import str_to_slug
from utils.misc_utils import nick


class MercRegisterSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = MercState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('merc').get(self.ui.langcode)
    
    self.state.user = nick(cog_data.get('interaction'))
    self.state.user_id = cog_data.get('interaction').user.id
    self.state.guild_id = cog_data.get('interaction').guild.id
    self.state.merc = cog_data.get('merc')
    
  # Session entry point
  async def start(self):
    self.ui.wait_message = True
    await self.ui.send()
    await self.ui.clear()
    self.ui.response = await self._get_response()
    await self.ui.send()

  # Get command response
  async def _get_response(self) -> dict:
    if str_to_slug(self.state.merc.get('name')) == self._translate('help'):
      return self.bot.message.get_help(whichone='merc register', lang=self.ui.langcode)
    self.state.found_hero = await self.bot.back_requests.call('getHeroByName', [str_to_slug(self.state.merc.get('name'))])
    if 'error' in self.state.found_hero:
      return self._return_error('hero not found') 
    self.state.heroes = await self.bot.back_requests.call('getAllHeroes')
    if 'error' in self.state.heroes:
      return self._return_error('request error')
    self.state.merc_list = await self._add_merc_to_user()
    if not self.state.merc_list or 'error' in self.state.merc_list:
      return self._return_error(self.state.merc_list.get('error'))
    return {'description': self._build_description(), 'color': 'default'}
  
  # Error builder
  def _return_error(self, error: str) -> dict:
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'hero not found':
        self.logger.log_only('error', f'[MERC REGISTER] Hero not found : {self.state.merc.get('name')}')
        description += (
          f'{self.error_msg.get('merc').get('part1')}{self.state.merc.get('name')}'
          f'{self.error_msg.get('merc').get('not found')}{self.error_msg.get('merc').get('part2')}'
        )
      case 'no pet found':
        self.logger.log_only('error', f'[MERC REGISTER] Hero has no pet : {self.state.found_hero.get('name')}')
        description += (
          f'{self.error_msg.get('merc').get('part1')}{self.state.found_hero.get('name')}'
          f'{self.error_msg.get('merc').get('no pet')}{self.error_msg.get('merc').get('part2')}'
        )
      case 'no A4':
        self.logger.log_only('error', f'[MERC REGISTER] Hero has no A4 : {self.state.found_hero.get('name')}')
        description += (
          f'{self.error_msg.get('merc').get('part1')}{self.state.found_hero.get('name')}'
          f'{self.error_msg.get('merc').get('no A4')}{self.error_msg.get('merc').get('part2')}'
        )
      case 'request error':
        self.logger.log_only('error', f'[MERC REGISTER] Error while requesting backend')
        description += self.error_msg.get('generic')
    return {'description': description, 'color': self.bot.message.get_message('error').get('color')}
  
  # Description builder
  def _build_description(self) -> str:
    return (
      f'## {self.return_msg.get('title')} {self.state.user} ##\n'
      f'{'\n'.join(MercCommon.display_mercs_by_color(session=self))}'
    )

  # Send merc helper
  async def _add_merc_to_user(self) -> bool:
    self.state.merc = self.state.clean_merc_values()
    if 'error' in self.state.merc:
      return self.state.merc
    self.state.merc['name'] = self.state.found_hero.get('name')
    self.state.merc['name_slug'] = self.state.found_hero.get('name_slug')
    to_add = {
      'user': self.state.user,
      'user_id': self.state.user_id,
      'guild_id': self.state.guild_id,
      'mercs': [self.state.merc]
    }
    self.logger.log_only('info', f'[MERC REGISTER] Merc to_add: {to_add}')
    result = await self.bot.back_requests.call('addMerc', [to_add])
    if result:
      return result
    return {'error': 'request error'}

  # Translate helper
  def _translate(self, key) -> str:
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)