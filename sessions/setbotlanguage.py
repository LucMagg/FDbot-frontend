from ui.base_ui import BaseUiData
from states.setbotlanguage import SetbotlanguageState

from utils.str_utils import str_to_slug


class SetbotlanguageSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = SetbotlanguageState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('setbotlanguage').get(self.ui.langcode)

    self.state.langcode = cog_data.get('language')
    self.state.channel_id = cog_data.get('interaction').channel_id

  # Session entry point  
  async def start(self):
    self.ui.wait_message = True
    await self.ui.send()
    await self.ui.clear()
    self.ui.response = await self._get_response()
    await self.ui.send()

  # Get command response
  async def _get_response(self) -> dict:
    if str_to_slug(self.state.langcode) == self._translate('help'):
      return self.bot.message.get_help(whichone='setbotlanguage', lang=self.ui.langcode)
    payload = {'channel_id': self.state.channel_id, 'code': self.state.langcode}
    self.state.language_set = await self.bot.back_requests.call('addLangChannel', [payload])
    if 'error' in self.state.language_set:
      return self._return_error()
    return {'description': self._build_description(), 'color': self.bot.message.get_message('setbotlanguage').get('color')}
  
  # Error builder
  def _return_error(self) -> dict:
    self.logger.log_only('error', f'[SETBOTLANGUAGE] Error while requesting backend')
    description = f'## {self.error_msg.get('title')} ##\n{self.error_msg.get('generic')}'
    return {'description': description, 'color': self.bot.message.get_message('error').get('color')}
  
  # Description builder
  def _build_description(self) -> str:
    return (
      f'## {self.return_msg.get('title')} ##\n'
      f'{self.return_msg.get('return1')}{self._translate(self.state.language_set.get('code'))}{self.return_msg.get('return2')}'
    )
  
  # Translate helper
  def _translate(self, key):
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)