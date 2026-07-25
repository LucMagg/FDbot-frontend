from ui.base_ui import BaseUiData
from states.addcomment import AddCommentState

from utils.str_utils import str_to_slug
from utils.misc_utils import nick
from sessions.hero import HeroSession
from sessions.pet import PetSession


class AddCommentSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = AddCommentState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)

    self.state.hero_or_pet = cog_data.get('hero_or_pet')
    self.state.comment = cog_data.get('comment')
    self.state.author = nick(cog_data.get('interaction'))

  # Session entry point  
  async def start(self):
    self.ui.wait_message = True
    await self.ui.send()
    await self.ui.clear()
    self.ui.response = await self._get_response()
    await self.ui.send()
  
  # Get command response
  async def _get_response(self):
    if str_to_slug(self.state.hero_or_pet) == self.bot.language.translate_from_key('help', self.ui.langcode):
      return self.bot.message.get_help(whichone='addcomment', lang=self.ui.langcode) 
    if self.state.comment is None:
      return self._return_error(error='empty comment')
    comment_result = await self._post_comment()
    match comment_result.get('type'):
      case 'hero':
        session_data = {
          'cog': self,
          'interaction': self.ui.interaction,
          'hero': comment_result.get('updated').get('name')
        }
        hero_session = HeroSession(session_data)
        return await hero_session._get_response()
      case 'pet':
        session_data = {
          'cog': self,
          'interaction':  self.ui.interaction,
          'pet': comment_result.get('updated').get('name')
        }
        pet_session = PetSession(session_data)
        return await pet_session._get_response()
      case 'error':
        if comment_result['updated']:
          return self._return_error(error='request error')
        return self._return_error(error='no hero or pet')
    
  # Error builder
  def _return_error(self, error: str) -> dict:
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'no hero or pet':
        self.logger.log_only('debug', f'[ADDCOMMENT] Argument not found in DB : {self.state.hero_or_pet}')
        description += f'{self.error_msg.get('addcomment').get('part1')}{self.state.hero_or_pet}{self.error_msg.get('addcomment').get('part2')}'
      case 'empty comment':
        self.logger.log_only('debug', '[ADDCOMMENT] Empty comment')
        description += self.error_msg.get('addcomment').get('notext')
      case 'request error':
        self.logger.log_only('error', f'[ADDCOMMENT] Error while requesting backend')
        description += self.error_msg.get('generic')
    return {'description': description, 'color': self.bot.message.get_message('error').get('color')}
  
  # Helper post comment 
  async def _post_comment(self) -> dict:
    payload = {'hero_or_pet': self.state.hero_or_pet, 'comment': self.state.comment, 'author': self.state.author, 'lang': self.ui.langcode}
    comment = await self.bot.back_requests.call('addComment', [payload])
    if not comment:
      return {'type': 'error', 'updated': None}
    updated = await self.bot.back_requests.call('getHeroByName', [self.state.hero_or_pet])
    if not 'error' in updated:
      return {'type': 'hero', 'updated': updated}
    updated = await self.bot.back_requests.call('getPetByName', [self.state.hero_or_pet])
    if not 'error' in updated:
      return {'type': 'pet', 'updated': updated}
    return {'type': 'error', 'updated': 'request error'}