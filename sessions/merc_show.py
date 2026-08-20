import discord

from ui.base_ui import BaseUiData
from states.merc import MercState

from ui.merc.common import MercCommon

from utils.str_utils import str_to_slug


class MercShowSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = MercState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('merc').get(self.ui.langcode)
    
    self.state.user_id = self._resolve_user_id(cog_data.get('user_id'))
    self.state.user = self._resolve_user_name()
    self.state.guild_id = cog_data.get('interaction').guild.id
    self.state.guild_name = cog_data.get('interaction').guild.name

  # Session entry point
  async def start(self):
    try:
      self.ui.wait_message = True
      await self.ui.send()
      await self.ui.clear()
      self.ui.response = await self._get_response()
      await self.ui.send()
    except Exception as e:
      self.logger.session_exception('Merc Show', e)

  # Get command response
  async def _get_response(self) -> dict:
    if str_to_slug(self.state.user) == self._translate('help'):
      return self.bot.message.get_help(whichone='merc show', lang=self.ui.langcode)
    self.state.merc_list = await self.bot.back_requests.call('getAllMercsByUser', [{'user_id': self.state.user_id, 'guild_id': self.state.guild_id}])
    if not self.state.merc_list or 'error' in self.state.merc_list:
      return self._return_error('no user')
    self.state.heroes = await self.bot.back_requests.call('getAllHeroes')
    if 'error' in self.state.heroes:
      return self._return_error('request error')
    return {'description': self._build_description(), 'color': 'default'}
  
  # Error builder
  def _return_error(self, error: str) -> dict:
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'no user':
        self.logger.log('error', f'[MERC SHOW] User not found : {self.state.user}')
        description += (
          f'{self.error_msg.get('merc').get('no user1')}{self.state.user}'
          f'{self.error_msg.get('merc').get('no user2')}{self.state.guild_name}'
          f'{self.error_msg.get('merc').get('no user3')}{self.error_msg.get('merc').get('part2')}'
        )
      case 'request error':
        self.logger.log('error', f'[MERC SHOW] Error while requesting backend')
        description += self.error_msg.get('generic')
    return {'description': description, 'color': self.bot.message.get_message('error').get('color')}
  
  # Description builder
  def _build_description(self) -> str:
    return (
      f'## {self.return_msg.get('title')} {self.state.user} ##\n'
      f'{'\n'.join(MercCommon.display_mercs_by_color(session=self))}'
    )
  
  # Get id from username helper
  def _resolve_user_id(self, user) -> int:
    try:
      return int(user)
    except:
      member = discord.utils.find(lambda m: m.name == user or m.display_name == user, self.ui.interaction.guild.members)
      return member.id if member else user
  
  # Get username from id helper
  def _resolve_user_name(self) -> str:
    try:
      member = discord.utils.find(lambda m: m.id == self.state.user_id, self.ui.interaction.guild.members)
      return member.display_name if member.display_name else member.name
    except:
      return self.state.user_id
  
  # Translate helper
  def _translate(self, key) -> str:
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)