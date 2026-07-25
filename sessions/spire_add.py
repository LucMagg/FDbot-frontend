import discord
import os
from datetime import datetime, timezone

from ui.base_ui import BaseUiData
from states.spire_add import SpireState

from ui.spire_add.views import MainView, SelectorView, YesNoView, ErrorView
from ui.spire_add.modals import Modal

from utils.misc_utils import nick, rank_text

spire_folder = os.path.join('images', 'spire')

class SpireAddSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = SpireState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('spire_add').get(self.ui.langcode)

    self.state.screenshot = cog_data.get('screenshot')

  # Session entry point
  async def start(self):
    self.ui.wait_message = True
    await self.ui.send()
    await self.ui.clear()
    if self.state.screenshot is None:
      return await self._return_help()
    await self._process_screenshot()

  # Return help endpoint
  async def _return_help(self):
    self.ui.response = self.bot.message.get_help(whichone='spire add', lang=self.ui.langcode)
    await self.ui.send()
    self.logger.ok_log('spire add', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)
  
  # Error endpoint
  async def _return_error(self, error: str, more: str = ''):
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'not a pic':
        self.logger.log_only('error', f'[SPIRE ADD] Screenshot is not a valid picture')
        description += self.error_msg.get('spire').get('not pic')
      case 'file':
        self.logger.log_only('error', f'[SPIRE ADD] Error while saving file')
        description += self.error_msg.get('spire').get('file error')
      case 'post':
        if more == 'add':
          self.logger.log_only('error', f'[SPIRE ADD] Error while posting score')
        else:
          self.logger.log_only('error', f'[SPIRE ADD] Error while getting rankings after posting score')
        description += self.error_msg.get('generic')
      case 'request error':
        self.logger.log_only('error', f'[SPIRE ADD] Error while requesting backend')
        description += self.error_msg.get('generic')
    self.ui.response = {'description': description, 'color': self.bot.message.get_message('error').get('color')}
    await self.ui.send()
    self.logger.nok_log('reward add', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)

  # First step : process screenshot (checks file extension, rename/save pic)
  async def _process_screenshot(self):
    _, ext = os.path.splitext(self.state.screenshot.filename.lower())
    if not self.state.screenshot.content_type or not self.state.screenshot.content_type.startswith('image/') or ext not in ['.png', '.jpg', '.jpeg']:
      return await self._return_error(error='not a pic')
    os.makedirs(spire_folder, exist_ok=True)
    self.state.file_name = f'{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{self.ui.interaction.user.id}'
    counter = 0
    while True:
      suffix = f'_{counter}' if counter else ''
      self.state.file_path = os.path.join(spire_folder, f'{self.state.file_name}{suffix}{ext}')
      if not os.path.exists(self.state.file_path):
        break
      counter += 1
    try:
      await self.state.screenshot.save(self.state.file_path)
    except:
      return self._return_error(error='file')
    await self._extract_data()

  # Second step : extract data (OCR pic & extract user/guild name) and get all guilds
  async def _extract_data(self):
    self.state.spire_data.username, self.state.spire_data.guild, self.state.spire_data.user_id = self._get_user_and_guildname()
    payload = {
      'username': self.state.spire_data.username,
      'guild': self.state.spire_data.guild,
      'user_id': self.state.spire_data.user_id,
      'image_url': self.state.screenshot.url
    }
    processed_pic = await self.bot.back_requests.call('extractSpireData', [payload])
    if 'error' in processed_pic:
      return await self._return_error(error='request error')
    self.state.spire_data.from_dict(processed_pic)
    self.logger.log_only('debug', f'[SPIRE ADD] Extracted data : {self.state.to_dict()}')
    guilds = await self.bot.back_requests.call('getAllExistingGuilds')
    if 'error' in guilds:
      return await self._return_error(error='request error')
    self.state.spire_data.all_guilds = sorted([g.get('name') for g in guilds])
    await self.flow_manager()

  # Flow manager
  async def flow_manager(self):
    # before render -> assignment
    match self.state.step:
      case 'guild'|'tier'|'climb':
        if self.state.selection =='CreateNewGuild':
          self.state.step = 'create'
        elif self.state.selection:
          self.state.set_item(self.state.step, self.state.selection)
          self.logger.log_only('debug', f'[SPIRE ADD] {self.state.step}: {self.state.selection}')
          self.state.step = 'main'
      case 'create':
        if self.state.inputs:
          self.state.set_item('guild', self.state.inputs.get('guild'))
          self.logger.log_only('debug', f'[SPIRE ADD] {self.state.step}: {self.state.spire_data.guild}')
          if not self.state.spire_data.is_guild_valid():
            self.state.spire_data.all_guilds.append(self.state.spire_data.guild)
            self.state.spire_data.all_guilds = sorted(self.state.spire_data.all_guilds)
            self.state.step = 'main'
          else:
            self.state.step = 'exists'
      case 'exists':
        if not self.state.validate:
          self.state.set_item('guild', None)
          self.logger.log_only('debug', f'[SPIRE ADD] Guild exists but canceled')
        else:
          self.state.clear_nav()
        self.state.step = 'main'
      case 'score':
        if self.state.inputs:
          self.state.spire_data.from_dict(self.state.inputs)
          self.logger.log_only('debug', f'[SPIRE ADD] {self.state.to_dict()}')
          if self.state.spire_data.is_score_valid():
            self.state.set_item('score', self.state.spire_data.calculate_score())
            self.logger.log_only('debug', f'[SPIRE ADD] score: {self.state.spire_data.score}')
            self.state.step = 'main'
          else:
            self.state.step = 'score error'
      case 'score error':
        self.state.step = 'score'
    # render
    await self.ui.clear()
    match self.state.step:
      case 'main':
        if self.state.validate:
          await self._render_finish()
        else:
          await self._render_main_view()
      case 'guild'|'tier'|'climb':
        await self._render_selector_view()
      case 'create'|'score':
        await self._render_modal()
      case 'exists':
        await self._render_yes_no_view()
      case 'score error':
        await self._render_error_view()

  # Render ui
  #    main view
  async def _render_main_view(self):
    self.logger.log_only('debug', f'[SPIRE ADD] Render main view')
    self.state.clear_nav()
    self._build_main()
    self.ui.view = MainView(self)
    await self.ui.send()

  #    selector view
  async def _render_selector_view(self):
    self.logger.log_only('debug', f'[SPIRE ADD] Render {self.state.step} view')
    self.state.clear_nav()
    match self.state.step:
      case 'guild':
        self._build_guild()
      case 'tier':
        self._build_tier()
      case 'climb':
        self._build_climb()
    self.ui.view = SelectorView(self)
    await self.ui.send()

  #    modal
  async def _render_modal(self):
    self.logger.log_only('debug', f'[SPIRE ADD] Render {self.state.step} modal')
    self.state.clear_nav()
    match self.state.step:
      case 'create':
        self._build_create()
      case 'score':
        self._build_score()
    self.ui.modal = Modal(self)
    await self.ui.send()

  #    yes/no view
  async def _render_yes_no_view(self):
    self.logger.log_only('debug', f'[SPIRE ADD] Render {self.state.step} yes/no view')
    self._build_exists()
    self.ui.view = YesNoView(self)
    await self.ui.send()

  #    error view
  async def _render_error_view(self):
    self.logger.log_only('debug', f'[SPIRE ADD] Render {self.state.step} view')
    self._build_score_error()
    self.ui.view = ErrorView(self)
    await self.ui.send()

  #    finish endpoint
  async def _render_finish(self):
    self.logger.log_only('debug', f'[SPIRE ADD] Render ranking')
    result = await self.bot.back_requests.call('addSpireData', [self.state.to_dict()])
    if 'error' in result:
      return self._return_error(error='post', more='add')
    add_channel_data = {'date': datetime.now(tz=timezone.utc).isoformat(), 'channel_id': self.ui.interaction.channel_id, 'guild': self.state.spire_data.guild}
    result = await self.bot.back_requests.call('addChannelToSpire', [add_channel_data])
    if 'error' in result:
      return self._return_error(error='post', more='add')
    result = await self.bot.back_requests.call('getSpireByDate',[{'date': datetime.now(tz=timezone.utc).isoformat()}])
    if 'error' in result:
      return self._return_error(error='post', more='get')
    date_to_display = next((d.get('start_date') for d in result.get('climbs') if d.get('number') == self.state.spire_data.climb), None)
    scores = await self.bot.back_requests.call('getSpireDataScores', [{'type': 'player', 'date': date_to_display}])
    if 'error' in result:
      return self._return_error(error='post', more='get')
    self._build_ranking(scores)
    await self.ui.send()
    self.logger.ok_log('spire add', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)
    
  # Timeout handler
  async def handle_timeout(self, whichone: str):
    self.logger.log_only('debug', f'[SPIRE ADD] {whichone} timeout')
    await self.ui.clear()
    self.ui.timeout_message = True
    await self.ui.send()
    self.logger.timeout_log('spire add', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)

  # View/modal builders
  #    main content/button labels
  def _build_main(self):
    self.ui.response = {'description': (
      f'## {self.return_msg.get('spire')} ## \n'
      f'** {self.return_msg.get('user')} **   {self.state.spire_data.username}\n'
      f'** {self.return_msg.get('guild')} **   {self.state.spire_data.guild if self.state.spire_data.is_guild_valid() else self.return_msg.get('none')}\n'
      f'** {self.return_msg.get('tier')} **   {self._translate(self.state.spire_data.tier) if self.state.spire_data.is_tier_valid() else self.return_msg.get('none')}\n'
      f'** {self.return_msg.get('climb')} **   {self.state.spire_data.climb if self.state.spire_data.is_climb_valid() else self.return_msg.get('none')}\n'
      f'** {self.return_msg.get('score')} **   {self.state.spire_data.score if self.state.spire_data.is_score_valid() else self.return_msg.get('none')}\n'
    ), 'color': self.bot.message.get_message('spire_add').get('color'), 'image': True}
    self.ui.files = [discord.File(self.state.file_path, filename=self.state.file_path.split('/')[-1])]
    self.state.guild_label = self.return_msg.get('guild title')
    self.state.tier_label = self.return_msg.get('tier title')
    self.state.climb_label = self.return_msg.get('climb title')
    self.state.score_label = self.return_msg.get('score title')
    self.state.validation_label = self.return_msg.get('validation')

  #    guild choices/content/placeholder
  def _build_guild(self):
    self.state.choices = [{'label': self.return_msg.get('new guild'), 'value': 'CreateNewGuild'}]
    self.state.choices += [{'label': g, 'value': g} for g in self.state.spire_data.all_guilds]
    self.ui.content = f'\n## {self.return_msg.get('guild title')} ## \n{self.return_msg.get('guild content')}'
    self.state.placeholder = self.state.spire_data.guild if self.state.spire_data.guild else self.return_msg.get('guild placeholder')
    self.state.previous_label = self.return_msg.get('previous')
    self.state.next_label = self.return_msg.get('next')

  #    create title/input label
  def _build_create(self):
    self.state.modal_inputs = [{'label': self.return_msg.get('create label'), 'placeholder': self.return_msg.get('create placeholder'), 'key': 'guild'}]
    self.ui.title = f'\n{self.return_msg.get('create title')}'
    
  #    exists content/button labels
  def _build_exists(self):
    self.ui.content = (
      f'\n## {self.return_msg.get('exists title')} ## \n'
      f'{self.return_msg.get('exists content 1')}{self.state.spire_data.guild}{self.return_msg.get('exists content 2')}'
    )
    self.state.yes_label = self._translate('Yes')
    self.state.no_label = self._translate('No')

  #    tier choices/content/placeholder
  def _build_tier(self):
    self.state.choices = [{'label': self._translate(t).capitalize(), 'value': t} for t in self.state.spire_data.all_tiers]
    self.ui.content = f'\n## {self.return_msg.get('tier title')} ## \n{self.return_msg.get('tier content')}'
    self.state.placeholder = self.state.spire_data.tier if self.state.spire_data.tier else self.return_msg.get('tier placeholder')

  #    climb choices/content/placeholder
  def _build_climb(self):
    self.state.choices = [{'label': str(i), 'value': str(i)} for i in range(1, 5)]
    self.ui.content = f'\n## {self.return_msg.get('climb title')} ## \n{self.return_msg.get('climb content')}'
    self.state.placeholder = self.state.spire_data.climb if self.state.spire_data.climb else self.return_msg.get('climb placeholder')

  #    score title/input labels
  def _build_score(self):
    self.ui.title = self.return_msg.get('score title')
    score_items = {'floors': 1, 'loss': 2, 'turns': 3, 'bonus': 4}
    self.state.modal_inputs = []
    for k, v in score_items.items():
      self.state.modal_inputs.append(
        {'label': self.return_msg.get(f'score label {v}'),
         'placeholder': str(getattr(self.state.spire_data, k)) if getattr(self.state.spire_data, k) else self.return_msg.get(f'score placeholder {v}'),
         'key': k}
      )

  #    score error content/button label
  def _build_score_error(self):
    description = f'\n## {self.return_msg.get('score error title')} ## \n'
    if not self.state.spire_data.is_floors_valid():
      description += f'{self.return_msg.get('score error floors')}\n'
    if not self.state.spire_data.is_loss_valid():
      description += f'{self.return_msg.get('score error loss')}\n'
    if not self.state.spire_data.is_turns_valid():
      description += f'{self.return_msg.get('score error turns')}\n'
    if not self.state.spire_data.is_bonus_valid():
      description += f'{self.return_msg.get('score error bonus')}\n'
    description += f'{self.return_msg.get('score error end')}\n'
    self.ui.response = {'description': description, 'color': self.bot.message.get_message('error').get('color')}
    self.state.ok_label = self.return_msg.get('ok')

  #    score ranking
  def _build_ranking(self, scores: dict):
    description = (
      f'# __{self._translate(self.state.spire_data.tier).capitalize()}__\n'
      f'## {self.return_msg.get('rank title 1')}{self.state.spire_data.climb}'
      f'{self._translate(rank_text(self.state.spire_data.climb))}{self.return_msg.get('rank title 2')}\n'
      f'{self._display_scores(scores)}'
    )
    self.ui.response = {'description': description, 'color': self.bot.message.get_message('spire_add').get('color'), 'image': True}
    self.ui.files = [discord.File(self.state.file_path, filename=self.state.file_path.split('/')[-1])]

  # Helpers
  #    get user and guildname (extract from interaction)
  def _get_user_and_guildname(self) -> tuple:
    user = nick(self.ui.interaction)
    user_id = self.ui.interaction.user.id
    if not ('[' in user and ']' in user):
      return user, None, user_id
    username = user.split('[')[0].strip()
    guild = user.split('[')[1]
    if guild[-1] == ']':
      guild = guild[:-1]
    elif username == '':
      username = user.split(']')[1].strip()
      guild = user.split('[')[1].split(']')[0].strip()
    else:
      guild = f'[{guild}'
    return username, guild, user_id
  
  #    display scores (extract from scores)
  def _display_scores(self, scores: dict) -> str:
    icons = [':first_place:', ':second_place:', ':third_place:']
    scores_data = scores.get('current_climb').get(self.state.spire_data.tier)
    return '\n'.join(
      f'{icons[i] if i < len(icons) else f'{i + 1}.'} '
      f'{item.get('score')} - '
      f'{item.get('username')} [{item.get('guild')}]'
      for i, item in enumerate(scores_data) if self._resolve_user(item.get('user_id'))
    )
  
  #    resolve user (checks if user exists in this channel to display scores)
  def _resolve_user(self, user_id: int) -> bool:
    return True if discord.utils.find(lambda m:m.id == user_id, self.ui.interaction.guild.members) else False

  #    translate
  def _translate(self, key) -> str:
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)