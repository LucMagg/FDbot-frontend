import discord
import random

from ui.base_ui import BaseUiData
from states.dhjk import DhjkState

from utils.misc_utils import stars

class DhjkSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger
    
    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = DhjkState()
    self.return_msg = self.bot.message.get_message('dhjk')

  # Session entry point
  async def start(self):
    try:
      self.ui.wait_message = True
      await self.ui.send()
      await self.ui.clear()
      self.ui.response = await self._get_response()
      self.ui.files = [self.state.file]
      await self.ui.send()
    except Exception as e:
      self.logger.session_exception('Dhjk', e)

  # Get command response
  async def _get_response(self) -> dict:
    self.state.rand = random.randint(0, 4)
    self.state.file = discord.File(self.cog.images[self.state.rand])
    description = f'# {stars(10)} #\n## {self.return_msg.get('title')} ##\n{self.return_msg.get(f'text{self.state.rand}')}'
    return {'description': description, 'color': self.return_msg.get('color'), 'image': True}