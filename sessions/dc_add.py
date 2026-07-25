import discord, os, re

from ui.base_ui import BaseUiData
from states.dc import DcState

from utils.str_utils import str_to_slug

dc_folder = os.path.join('images', 'dc')

class DcAddSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = DcState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('dc').get(self.ui.langcode)

    self.state.level = cog_data.get('level')
    self.state.screenshots = cog_data.get('screenshots')
    self.state.replay = cog_data.get('replay')

    self.pattern = r'<fnd://replay\?([A-Za-z0-9+/=]+)>'

  # Session entry point
  async def start(self):
    try:
      self.ui.wait_message = True
      await self.ui.send()
      await self.ui.clear()
      for i, s in enumerate(self.state.screenshots):
        filepath = await self._process_screenshot(i, s)
        if isinstance(filepath, dict):
          break
        else:
          self.state.screenshots_filepath.append(filepath)
      reg_match = True
      if self.state.replay:
        reg_match = re.search(self.pattern, self.state.replay)
        if not reg_match:
          self.ui.response = self._return_error(error='invalid link')
        else:
          self.state.replay = f'fnd://{self.state.replay.split('fnd://')[1][:-1]}'
      if not isinstance(filepath, dict) and reg_match:
        await self._get_response()
      await self.ui.send()
    except Exception as e:
      self.logger.log_only('error', f'[DC ADD] Error : {e}')

  # Get command response
  async def _get_response(self) -> dict:
    if str_to_slug(self.state.level) == self._translate('help'):
      self.ui.response = self.bot.message.get_help(whichone='dc add', lang=self.ui.langcode)
      return
    self.state.dc_level = await self.bot.back_requests.call('addDC', [self.state.to_dict()])
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
      case 'not a pic':
        self.logger.log_only('error', f'[DC ADD] Screenshot is not a valid picture')
        description += self.error_msg.get('not pic')
      case 'file':
        self.logger.log_only('error', f'[DC ADD] Error while saving file')
        description += self.error_msg.get('file error')
      case 'invalid link':
        self.logger.log_only('error', f'[DC ADD] Couldn\'t regex {self.state.replay}')
        description += self.error_msg.get('addreplay')
      case 'request error':
        self.logger.log_only('error', f'[DC ADD] Error while requesting backend')
        description += self.error_msg.get('generic')
    self.ui.response = {'description': description, 'color': self.bot.message.get_message('error').get('color')}
    return
  
  # Process screenshot helper (checks file extension, rename/save pic)
  async def _process_screenshot(self, index: int, screenshot: discord.File) -> str|None:
    if screenshot is None:
      return None
    _, ext = os.path.splitext(screenshot.filename.lower())
    if not screenshot.content_type or not screenshot.content_type.startswith('image/') or ext not in ['.png', '.jpg', '.jpeg']:
      return await self._return_error(error='not a pic')
    os.makedirs(dc_folder, exist_ok=True)
    file_name = f'DC{self.state.level}_Floor{index + 1}'
    counter = 0
    while True:
      suffix = f'_{counter}' if counter else ''
      file_path = os.path.join(dc_folder, f'{file_name}{suffix}{ext}')
      if not os.path.exists(file_path):
        break
      counter += 1
    try:
      await screenshot.save(file_path)
      return file_path
    except:
      return self._return_error(error='file')

  # Description builder
  def _build_description(self) -> str:
    return f'## {self.return_msg.get('title')} {self.state.dc_level.get('name')} \n'
  
  # Translate helper
  def _translate(self, key) -> str:
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)