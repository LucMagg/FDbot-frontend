from ui.base_ui import BaseUiData
from states.reward import RewardState

from ui.reward.common import RewardCommon

from utils.str_utils import slug_to_str, str_to_slug
from utils.misc_utils import nick


class RewardShowSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = RewardState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('reward').get(self.ui.langcode)

    self.state.user = nick(self.ui.interaction)
    self.state.level_name = cog_data.get('level')

  # Session entry point
  async def start(self):
    self.ui.wait_message = True
    await self.ui.send()
    await self.ui.clear()
    self.ui.response, self.ui.files = await self._get_response()
    await self.ui.send()

  # Get response
  async def _get_response(self):
    if str_to_slug(self.state.level_name) == self._translate('help'):
      return self.bot.message.get_help(whichone='reward show', lang=self.ui.langcode), None
    check = self._check_level_name()
    if check:
      return await self._return_error(error='not found'), None
    self.state.all_levels = await self.bot.back_requests.call('getAllLevels')
    if 'error' in self.state.all_levels:
      return await self._return_error(error='request error'), None
    self.state.level = next((l for l in self.state.all_levels if (slug_to_str(self.state.level_name) in l.get('name') or self.state.level_name == l.get('name_slug'))), None)
    if not self.state.level:
      return await self._return_error(error='not found'), None
    self.state.level_name = self.state.level.get('name').get(self.ui.langcode, self.state.level.get('name').get('en'))

    common = RewardCommon(self)
    reward_list, chart_img = common.display_rewards()
    description = f'## {self.state.level_name} ##\n{reward_list}'
    return {'description': description, 'color': self.bot.message.get_message('reward').get('color'), 'image': True}, [chart_img]
 
  # Error builder
  async def _return_error(self, error: str):
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'not found':
        self.logger.log_only('debug', f'[REWARD SHOW] {self.state.level_name} not found')
        description += f'{self.error_msg.get('reward').get('part1')}{self.state.level_name}{self.error_msg.get('reward').get('part2')}'
      case 'request error':
        self.logger.log_only('error', f'[REWARD SHOW] Error while requesting backend')
        description += self.error_msg.get('generic')
    return {'description': description, 'color': self.bot.message.get_message('error').get('color')}

  # Check level name helper
  def _check_level_name(self) -> bool:
    found = any((slug_to_str(self.state.level_name) == choice.name or str_to_slug(self.state.level_name) == choice.value)
                for choices in self.cog.level_choices.values()
                for choice in choices)
    if found:
      return False
    return True

  # Translate helper
  def _translate(self, key) -> str:
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)