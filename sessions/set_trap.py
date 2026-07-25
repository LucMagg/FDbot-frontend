import discord

from ui.base_ui import BaseUiData
from states.set_trap import Set_trapState

from utils.str_utils import str_to_slug


class Set_trapSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = Set_trapState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('set_trap').get(self.ui.langcode)

    self.state.trap_id = cog_data.get('trap_id')
    self.state.guild_id = cog_data.get('interaction').guild.id

  # Session entry point  
  async def start(self):
    try:
      self.ui.wait_message = True
      await self.ui.send()
      await self.ui.clear()
      self.ui.response = await self._get_response()
      await self.ui.send()
    except Exception as e:
      self.bot.logger.log_only('error', f'[SET_TRAP] Error: {e}')

  # Get command response
  async def _get_response(self) -> dict:
    if str_to_slug(self.state.trap_id) == self._translate('help'):
      return self.bot.message.get_help(whichone='set_trap', lang=self.ui.langcode)
    try:
      role = await self.ui.interaction.guild.fetch_role(int(self.state.trap_id))
    except discord.NotFound:
      return self._return_error('not found')
    payload = {'guild_id': int(self.state.guild_id), 'role_id': int(self.state.trap_id)}
    self.state.trap_set = await self.bot.back_requests.call('addTrapRole', [payload])
    if 'error' in self.state.trap_set:
      return self._return_error('request error')
    self.bot.trap_roles = await self.bot.back_requests.call('getAllTrapRoles')
    if 'error' in self.state.trap_set:
      return self._return_error('request error')
    return {'description': self._build_description(role), 'color': self.bot.message.get_message('set_trap').get('color')}
  
  # Error builder
  def _return_error(self, error) -> dict:
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'not found':
        self.logger.log_only('error', f'[SET_TRAP] Role {self.state.trap_id} not found')
        description += f'{self.error_msg.get('set_trap').get('not found1')}{self.state.trap_id}{self.error_msg.get('set_trap').get('not found2')}'
      case 'request error':
        self.logger.log_only('error', f'[SET_TRAP] Error while requesting backend')
        description += self.error_msg.get('generic')
    return {'description': description, 'color': self.bot.message.get_message('error').get('color')}
  
  # Description builder
  def _build_description(self, role) -> str:
    return (
      f'## {self.return_msg.get('title')} ##\n'
      f'{self.return_msg.get('return1')}{role}{self.return_msg.get('return2')}'
    )
  
  # Translate helper
  def _translate(self, key):
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)