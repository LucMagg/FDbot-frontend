import discord, os

from ui.base_ui import BaseUiData
from states.dc import DcState

from utils.str_utils import str_to_slug

dc_folder = os.path.join('images', 'dc')

class DcShowSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = DcState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('dc').get(self.ui.langcode)

    self.state.level = cog_data.get('level')

  # Session entry point
  async def start(self):
    try:
      self.ui.wait_message = True
      await self.ui.send()
      await self.ui.clear()
      await self._get_response()
      await self.ui.send()
    except Exception as e:
      self.logger.log_only('error', f'[DC SHOW] Error : {e}')

  # Get command response
  async def _get_response(self) -> dict:
    if str_to_slug(self.state.level) == self._translate('help'):
      self.ui.response = self.bot.message.get_help(whichone='dc show', lang=self.ui.langcode)
      return
    self.state.dc_level = await self.bot.back_requests.call('getDC', [{'name': self.state.level}])
    if 'error' in self.state.dc_level:
      self.ui.response = self._return_error(error='request error')
      return
    self.ui.response = {'description': self._build_description(), 'color': self.bot.message.get_message('dc').get('color')}
    self.ui.files = []
    replays = self.state.dc_level.get('replays')
    if any(r is not None for r in replays):
      self.ui.followup_content = [f'__** {self.return_msg.get('replay')} **__']
      for r in replays:
        if r is not None:
          self.ui.followup_content.append(r)
    for s in self.state.dc_level.get('screenshots'):
      if s is not None:
        self.ui.files.append(discord.File(s))
        self.ui.response['image'] = True

  # Error builder
  def _return_error(self, error: str) -> dict:
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'request error':
        self.logger.log_only('error', f'[DC SHOW] Error while requesting backend')
        description += self.error_msg.get('generic')
    self.ui.response = {'description': description, 'color': self.bot.message.get_message('error').get('color')}
    return

  # Description builder
  def _build_description(self) -> str:
    return f'## {self.return_msg.get('title')} {self.state.dc_level.get('name')} \n'
  
  # Translate helper
  def _translate(self, key) -> str:
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)