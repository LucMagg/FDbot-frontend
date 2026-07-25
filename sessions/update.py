from typing import Dict

from ui.base_ui import BaseUiData
from states.update import UpdateState

from utils.str_utils import str_to_slug


class UpdateSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = UpdateState()
    self.return_msg = self.bot.message.get_message('update').get(self.ui.langcode)

    self.state.type = cog_data.get('type')

  # Session entry point
  async def start(self):
    self.ui.wait_message = True
    self.ui.more_response = self.return_msg.get('warning')
    await self.ui.send()
    await self.ui.clear()
    self.ui.response = await self._get_response()
    await self.ui.send()
    self.logger.ok_log('update', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)

  # Get command response
  async def _get_response(self) -> Dict:
    if not self.state.type:
      self.state.type = 'all'
    if str_to_slug(self.state.type) == self.bot.language.translate_from_key(text_to_translate='help', lang='en') or \
      str_to_slug(self.state.type) == self.bot.language.translate_from_key(text_to_translate='help', lang='fr'):
        return self.bot.message.get_help(whichone='update', lang=self.ui.langcode)
    description = f'## {self.return_msg.get('title')} ##\n'
    update = await self._get_update()
    if not update:
      description += self.return_msg.get('error')
      return {'description': description, 'color': 'red'}   
    if self.state.type == 'all':
      description += f'{self.return_msg.get('all')}\n'
      types_to_update = ['hero', 'pet', 'talent']
    else:
      description += f'{self.return_msg.get('part1')} {self.return_msg.get(self.state.type)} {self.return_msg.get('part2')}\n'
      types_to_update = [self.state.type]
    description += self.return_msg.get('thxmsg')
    await self.bot.update_service.command_setup_updater(types_to_update, True)
    return {'description': description, 'color': self.bot.message.get_message('update').get('color')}
  
  # Request for update
  async def _get_update(self):
    if str_to_slug(self.state.type) == 'all':
      return await self.bot.back_requests.call('getAllUpdates')
    else:
      return await self.bot.back_requests.call('getOneUpdate', [self.state.type])