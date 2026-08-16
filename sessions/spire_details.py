import discord, re, unicodedata
from datetime import datetime, timezone, timedelta
from typing import Optional
from difflib import get_close_matches

from ui.base_ui import BaseUiData
from states.spire_details import SpireState

from ui.spire_details.views import MainView, MapView, WaterOrLavaView, BonusValidationView, BonusValidationView, BracketView, TalentsBetweenView, FinalView
from ui.spire_details.modals import BonusModal, TalentsModal

from utils.misc_utils import rank_text
from utils.str_utils import str_to_slug


class SpireDetailsSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'), bot=self.bot)
    self.state = SpireState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('spire_details').get(self.ui.langcode)

  # Session entry point
  async def start(self):
    self.date = datetime.now(tz=timezone.utc)
    self.ui.wait_message = True
    await self.ui.send()
    await self.ui.clear()
    await self._load_spire_data()

  # Spire loader
  async def _load_spire_data(self):
    spire = await self.bot.back_requests.call('getSpireByDate', [{'date': self.date.isoformat()}])
    if 'error' in spire:
      return await self._return_error('request error')
    self.state.details_data.spire = spire
    self.state.details_data.climb = self._get_current_climb()
    self.state.details_data.all_maps = await self.bot.back_requests.call('getAllMaps')
    if 'error' in self.state.details_data.all_maps:
      return await self._return_error('request error')
    climb_data = next((c for c in spire.get('climbs', []) if c.get('number') == self.state.details_data.climb), None)
    if climb_data and climb_data.get('climb_details'):
      self.state.details_data.from_climb_details(climb_data['climb_details'], self.state.details_data.all_maps)
    else:
      self.state.details_data.talents = {}
    talents = await self.bot.back_requests.call('getAllTalents')
    if 'error' in talents:
      return await self._return_error('request error')
    self.state.details_data.all_talents = talents
    await self.flow_manager()

  # Error endpoint
  async def _return_error(self, error: str):
    match error:
      case 'request error':
        self.logger.log_only('error', f'[SPIRE DETAILS] Error while requesting backend')
        description += self.error_msg.get('generic')
    self.ui.response = {'description': description, 'color': self.bot.message.get_message('error').get('color')}
    await self.ui.send()
    self.logger.nok_log('spire details', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)

  # Flow manager
  async def flow_manager(self):
    # before render -> assignment
    match self.state.step:
      case 'map':
        if self.state.selection:
          selected = next((m for m in self.state.details_data.all_maps if m.get('name') == self.state.selection), None)
          self.state.details_data.selected_map = selected
          if self.state.details_data.selected_map and self.state.details_data.selected_map.get('has_water_or_lava'):
            self.state.step = 'water_or_lava'
          else:
            self.state.details_data.map_url = next((m.get('image_url') for m in self.state.details_data.selected_map.get('pics') if m.get('name') == 'neutral'), None)
            self.state.step = 'main'
          self.state.clear_nav()
        else:
          self.state.page = 0
          self.state.step = 'initial'
          self.state.clear_nav()
      case 'water_or_lava':
        self.state.details_data.map_url = next((m.get('image_url') for m in self.state.details_data.selected_map.get('pics') if m.get('name') == self.state.selection), None)
        self.state.details_data.selected_map['water_or_lava'] = self.state.selection
        self.state.step = 'main'
        self.state.clear_nav()
      case 'hero_bonus':
        self.state.step = 'main' if self.state.inputs == self.state.details_data.hero_bonus else 'hero_bonus_validation'
      case 'hero_bonus_validation':
        if self.state.validate:
          if self.state.inputs is not None:
            if self.state.inputs.get('type'):
              self.state.details_data.hero_bonus['type'] = self.state.inputs['type']
            if self.state.inputs.get('buff'):
              self.state.details_data.hero_bonus['buff'] = self.state.inputs['buff']
          self.state.step = 'main'
        else:
          self.state.step = 'hero_bonus'
        self.state.clear_nav()
      case 'monster_bonus':
        self.state.step = self.state.step = 'main' if self.state.inputs == self.state.details_data.hero_bonus else 'monster_bonus_validation'
      case 'monster_bonus_validation':
        if self.state.validate:
          if self.state.inputs is not None:
            if self.state.inputs.get('type'):
              self.state.details_data.monster_bonus['type'] = self.state.inputs['type']
            if self.state.inputs.get('buff'):
              self.state.details_data.monster_bonus['buff'] = self.state.inputs['buff']
          self.state.step = 'main'
        else:
          self.state.step = 'monster_bonus'
        self.state.clear_nav()
      case 'bracket':
        self.state.selected_tier = self.state.selection
        if not self.state.details_data.talents.get(self.state.selected_tier):
          self.state.details_data.talents[self.state.selected_tier] = [''] * self.state.max_talents_floor
        self.state.talents_step = 1
        self.state.step = 'talents'
      case 'talents':
        if self.state.inputs:
          start = (self.state.talents_step - 1) * 5
          end = min(start + 5, self.state.max_talents_floor)
          for i in range(start, end):
            key = f'floor_{i + 1}'
            talent = self._match_talent(self.state.inputs.get(key))
            self.state.details_data.talents[self.state.selected_tier][i] = talent or self.state.details_data.talents[self.state.selected_tier][i]
          self.state.step = 'talents_between'
          self.state.clear_nav()
      case 'talents_between':
        if self.state.validate:
          if self.state.talents_step < 3:
            self.state.talents_step += 1
            self.state.step = 'talents'
          else:
            self.state.step = 'main'
          self.state.clear_nav()
        else:
          self.state.talents_step = 1 if self.state.talents_step == 3 else self.state.talents_step
          self.state.step = 'talents'
          self.state.clear_nav()
      case 'main':
        if self.state.validate:
          self.state.step = 'finish'
          self.state.clear_nav()
        elif self.state.selection:
          match self.state.selection:
            case 'map':
              self.state.step = 'map'
            case 'hero_bonus':
              self.state.step = 'hero_bonus'
            case 'monster_bonus':
              self.state.step = 'monster_bonus'
            case 'talents':
              self.state.step = 'bracket'
          self.state.clear_nav()
    # render
    await self.ui.clear()
    match self.state.step:
      case 'main':
        await self._render_main_view()
      case 'map':
        await self._render_map_view()
      case 'water_or_lava':
        await self._render_water_or_lava_view()
      case 'hero_bonus':
        await self._render_hero_bonus_modal()
      case 'hero_bonus_validation':
        await self._render_hero_bonus_validation_view()
      case 'monster_bonus':
        await self._render_monster_bonus_modal()
      case 'monster_bonus_validation':
        await self._render_monster_bonus_validation_view()
      case 'bracket':
        await self._render_bracket_view()
      case 'talents':
        await self._render_talents_modal()
      case 'talents_between':
        await self._render_talents_between_view()
      case 'cancel':
        await self._render_cancel_view()
      case 'finish':
        await self._render_finish()

  # Render ui
  #    main view
  async def _render_main_view(self):
    self.logger.log_only('debug', '[SPIRE DETAILS] Render initial view')
    self._build_main()
    self.ui.view = MainView(self)
    await self.ui.send()

  #    map view
  async def _render_map_view(self):
    self.logger.log_only('debug', '[SPIRE DETAILS] Render map view')
    self._build_map()
    self.ui.view = MapView(self)
    await self.ui.send()

  #    water or lava view
  async def _render_water_or_lava_view(self):
    self.logger.log_only('debug', '[SPIRE DETAILS] Render water or lava view')
    self._build_water_or_lava()
    self.ui.view = WaterOrLavaView(self)
    await self.ui.send()

  #    hero bonus modal
  async def _render_hero_bonus_modal(self):
    self.logger.log_only('debug', '[SPIRE DETAILS] Render hero bonus modal')
    self._build_bonus()
    self.ui.modal = BonusModal(self)
    await self.ui.send()

  #    hero bonus validation view
  async def _render_hero_bonus_validation_view(self):
    self.logger.log_only('debug', '[SPIRE DETAILS] Render hero bonus validation view')
    self._build_bonus_validation('hero')
    self.ui.view = BonusValidationView(self)
    await self.ui.send()

  #    monster bonus modal
  async def _render_monster_bonus_modal(self):
    self.logger.log_only('debug', '[SPIRE DETAILS] Render monster bonus modal')
    self._build_bonus()
    self.ui.modal = BonusModal(self)
    await self.ui.send()

  #    monster bonus validation view
  async def _render_monster_bonus_validation_view(self):
    self.logger.log_only('debug', '[SPIRE DETAILS] Render monster bonus validation view')
    self._build_bonus_validation('monster')
    self.ui.view = BonusValidationView(self)
    await self.ui.send()

  #    bracket view
  async def _render_bracket_view(self):
    self.logger.log_only('debug', '[SPIRE DETAILS] Render bracket view')
    self._build_bracket()
    self.ui.view = BracketView(self)
    await self.ui.send()

  #    talents modal
  async def _render_talents_modal(self):
    self.logger.log_only('debug', f'[SPIRE DETAILS] Render talents modal (step {self.state.talents_step}/3)')
    self._build_talents()
    self.ui.modal = TalentsModal(self)
    await self.ui.send()

  #    talents between view
  async def _render_talents_between_view(self):
    self.logger.log_only('debug', f'[SPIRE DETAILS] Render talents between view (step {self.state.talents_step}/3)')
    self._build_talents_between()
    self.ui.view = TalentsBetweenView(self)
    await self.ui.send()
  
  #    cancel view
  async def _render_cancel_view(self):
    self.logger.log_only('debug', f'[SPIRE DETAILS] Render cancel view')
    self._build_cancel()
    await self.ui.send()
    self.logger.nok_log('spire details', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)

  #    final view
  async def _render_finish(self):
    self.logger.log_only('debug', '[SPIRE DETAILS] Render finish / final view')
    self._build_main_embed()
    await self._save_and_post()
    self.logger.ok_log('spire details', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)

  # Timeout handler
  async def handle_timeout(self, whichone: str):
    self.logger.log_only('debug', f'[SPIRE DETAILS] {whichone} timeout')
    await self.ui.clear()
    self.ui.timeout_message = True
    await self.ui.send()
    self.logger.timeout_log('spire details', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)

  
  # View/modal builders
  #    main content/button labels
  def _build_main(self):
    self.ui.content = ''
    self._build_main_embed()
    self.state.map_label = self.return_msg.get('map_label')
    self.state.hero_bonus_label = self.return_msg.get('hero_bonus_label')
    self.state.monster_bonus_label = self.return_msg.get('monster_bonus_label')
    self.state.talents_label = self.return_msg.get('talents_label')
    self.state.finish_label = self.return_msg.get('finish_label')
    self.state.cancel_label = self.return_msg.get('cancel_label')

  #    map choices/content/placeholder/button labels
  def _build_map(self):
    selected_name = self.state.details_data.selected_map.get('name') if self.state.details_data.selected_map else None
    self.state.choices = [{'label': m.get('name'), 'value': m.get('name')} for m in sorted(self.state.details_data.all_maps, key=lambda m: m.get('name'))]
    self.state.placeholder = selected_name or self.return_msg.get('map placeholder')
    self.ui.content = ''
    self._response_builder('map')
    self.ui.response['description'] += self.return_msg.get(f'map content 2')
    if self.state.details_data.selected_map:
      self.ui.response['image'] = self._map_url()
    self.state.cancel_label = self.return_msg.get('cancel_label')
    self.state.previous_label = self.return_msg.get('previous_label')
    self.state.next_label = self.return_msg.get('next_label')

  #    water_or_lava content/button labels
  def _build_water_or_lava(self):
    self.ui.content = ''
    self._response_builder('water_or_lava')
    self.ui.response['description'] += self.return_msg.get(f'water_or_lava content 2')
    self.ui.response['image'] = self._map_url()
    self.state.water_label = self.return_msg.get('water_label')
    self.state.lava_label = self.return_msg.get('lava_label')

  #    bonus modal title/input labels
  def _build_bonus(self):
    whichone = self.state.step.split('_')[0]
    self.ui.title = self.return_msg.get(f'{whichone} bonus title')
    self.state.modal_inputs = []
    for idx, key in enumerate(['type', 'buff']):
      self.state.modal_inputs.append({
        'label': self.return_msg.get(f'{whichone} bonus label {idx + 1}'),
        'default': getattr(self.state.details_data, self.state.step).get(key, None),
        'placeholder': self.return_msg.get(f'{whichone} bonus placeholder {idx + 1}'),
        'key': key,
        'required': False,
      })

  #    bonus view content/button labels
  def _build_bonus_validation(self, whichone: str):
    self.ui.content = ''
    self._response_builder(f'{whichone} bonus')
    buff = self.state.inputs.get('buff') or None
    type = self.state.inputs.get('type') or None
    self.ui.response['description'] += self._hero_bonus_description_builder(type, buff) if whichone == 'hero' else self._monster_bonus_description_builder(type, buff)
    self.ui.response['description'] += f'\n{self.return_msg.get(f'{whichone} bonus content 2')}\n'
    self.state.no_label = self.return_msg.get('no_label')
    self.state.yes_label = self.return_msg.get('yes_label')

  #    bracket choices/content/placeholder
  def _build_bracket(self):
    self.ui.content = ''
    self._response_builder('bracket')
    self.ui.response['description'] += f'\n{self.return_msg.get(f'bracket content 2')}\n'
    self.state.choices = [{
      'label': self._translate(t).capitalize(),
      'value': t,
      'emoji': '🟢' if self.state.details_data.talents.get(t) else '🔴'} for t in self.state.details_data.all_tiers]
    self.state.placeholder = self.return_msg.get('bracket placeholder')
  
  #    talents modal title/input labels
  def _build_talents(self):
    self.ui.title = f'{self._translate(self.state.selected_tier).capitalize()}{self.return_msg.get('talent title')} ({self.state.talents_step}/3)'
    start = (self.state.talents_step - 1) * 5
    end = min(start + 5, self.state.max_talents_floor)
    tier_talents = self.state.details_data.talents.get(self.state.selected_tier, [''] * self.state.max_talents_floor)
    self.state.modal_inputs = [{
      'label': f'{self.return_msg.get('floor')} {i+1}',
      'default': str(tier_talents[i]) if tier_talents[i] else '',
      'key': f'floor_{i + 1}',
      'required': True} for i in range(start, end)]

  #    talents view between modals content/button labels
  def _build_talents_between(self):
    self.ui.content = ''
    self._response_builder('talent')
    self.ui.response['description'] = f'## {self._translate(self.state.selected_tier).capitalize()}{self.return_msg.get('talent title')} \n'
    max_range = min(self.state.talents_step * 5, self.state.max_talents_floor)
    tier_talents = self.state.details_data.talents.get(self.state.selected_tier, [])
    self.ui.response['description'] += '\n'.join(f'{i+1}. {self._translate(tier_talents[i])}' for i in range(max_range))
    self.state.continue_label = self.return_msg.get('continue_label')
    self.state.change_label = self.return_msg.get('change_label')
    self.state.validate_label = self.return_msg.get('validate_label')

  #    main embed
  def _build_main_embed(self, ui: Optional[BaseUiData] = None):
    ui = ui or self.ui
    self._response_builder('main', ui=ui)
    lines = [self.return_msg.get(f'main content 2')] if self.state.step == 'main' else []
    if self.state.details_data.selected_map:
      ui.response['image'] = self._map_url()
    if self.state.details_data.hero_bonus:
      lines.append(f'### {self.return_msg.get('main content 3')} ')
      lines.append(self._hero_bonus_description_builder(self.state.details_data.hero_bonus.get('type'), self.state.details_data.hero_bonus.get('buff')))
    if self.state.details_data.monster_bonus:
      lines.append(f'### {self.return_msg.get('main content 4')}')
      lines.append(self._monster_bonus_description_builder(self.state.details_data.monster_bonus.get('type'), self.state.details_data.monster_bonus.get('buff')))
    tiers = [t for t in self.state.details_data.all_tiers if t in self.state.details_data.talents]
    if tiers:
      lines.append(f'### {self.return_msg.get('main content 5')}')
      for tier in tiers:
        lines.append(f'__** {self._translate(tier, ui.langcode).capitalize()} **__')
        lines.append(''.join(f'{i + 1}. {self._translate(t, ui.langcode)}\n' for i, t in enumerate(self.state.details_data.talents[tier])))
    if self.state.details_data.selected_map:
      lines.append(f'### {self.return_msg.get('map_label')}')
    ui.response['description'] += '\n'.join(lines)

  #    cancel embed builder
  def _build_cancel(self):
    self._response_builder('main')
    self.ui.response['description'] += self.return_msg.get('cancel content')
    self.ui.response['color'] = self.return_msg.get('cancel color')

  #    response builder
  def _response_builder(self, whichone: str, ui: Optional[BaseUiData] = None) -> None:
    ui = ui or self.ui
    ui.response = {}
    ui.response['description'] = (
      f'## {self.return_msg.get(f'{whichone} content 1')} {self.state.details_data.climb}'
      f'{self._translate(rank_text(self.state.details_data.climb), ui.langcode)} {self.return_msg.get('climb')} \n'
    )  
    ui.response['color'] = self.bot.message.get_message('spire_details').get('color')
  
  #    map url
  def _map_url(self) -> str:
    if not self.state.details_data.selected_map:
      return None
    pics = self.state.details_data.selected_map.get('pics', [])
    water_or_lava = self.state.details_data.selected_map.get('water_or_lava')
    if water_or_lava:
      match = next((p.get('image_url') for p in pics if p.get('name') == water_or_lava), None)
      if match:
        return match
    if self.state.details_data.map_url:
      selected_pic = next((p for p in pics if p.get('image_url') == self.state.details_data.map_url), None)
      if selected_pic:
        return self.state.details_data.map_url
    return next((p.get('image_url') for p in self.state.details_data.selected_map.get('pics') if p.get('name') == 'neutral'), None)

  #    hero bonus builder
  def _hero_bonus_description_builder(self, type: str, buff: str) -> str:
    result = ''
    if type:
      result += f'{self.return_msg.get(f'hero bonus label 1').replace('[XXX]', type)}\n'
    if type and buff:
      result += f'{self.return_msg.get(f'hero bonus label 2').replace('[XXX]', type).replace('[YYY]', buff)}\n'
    if not type and not buff:
      result += f'{self.return_msg.get(f'hero bonus no content')}\n'
    return result
  
  #    monster bonus builder
  def _monster_bonus_description_builder(self, type: str, buff: str) -> str:
    result = ''
    if type and buff:
      result += f'{self.return_msg.get(f'monster bonus label 1').replace('[XXX]', type).replace('[YYY]', buff)}\n'
    else:
      result += f'{self.return_msg.get(f'monster bonus no content')}\n'
    return result

  # Save and post final embed (finish endpoint)
  async def _save_and_post(self):
    await self.bot.back_requests.call('addClimbDetails', [{
      'date': self.date.isoformat(),
      'climb_details': self.state.details_data.to_dict()
    }])
    await self._handle_spire_channels()

  #    update channels helper
  async def _handle_spire_channels(self):
    current_spire_channel = next((c for c in self.state.details_data.spire.get('channels') if c.get('discord_channel_id') == self.ui.message.channel.id), None)
    if current_spire_channel is None:
      await self.bot.back_requests.call('addChannelToSpire', [{'date': self.date.isoformat(), 'channel_id': self.ui.message.channel.id}])
    for channel_data in self.state.details_data.spire.get('channels', []):
      if channel_data != current_spire_channel:
        channel = self.bot.get_channel(channel_data['discord_channel_id'])
        channel_ui = BaseUiData.from_channel(channel, self.bot)
        await self._build_channel_ui(channel_data, channel, channel_ui)
        await channel_ui.send()
        message = channel_ui.message
      else:
        await self._build_channel_ui(current_spire_channel, self.ui.message.channel, self.ui)
        await self.ui.send()
        message = self.ui.message
      await self.bot.back_requests.call('addMessageId', [{'date': self.date.isoformat(), 'channel_id': message.channel.id, 'climb_details_message_id': message.id}])
  
  #    build channel ui
  async def _build_channel_ui(self, channel_data: dict, channel: discord.TextChannel, ui: BaseUiData) -> None:
    ui.pin = True
    if channel_data.get('climb_details_message_id'):
      ui.previous_message = await channel.fetch_message(channel_data.get('climb_details_message_id'))
      ui.unpin = True
    self.return_msg = self.bot.message.get_message('spire_details').get(ui.langcode)
    self._build_main_embed(ui=ui)

  # Helpers
  #    talents helpers
  def _match_talent(self, input: str) -> str:
    try:
      talent_slugs = [str_to_slug(t.get('name')) for t in self.state.details_data.all_talents]
      result = self._get_talent_in_list(input, talent_slugs)
      if not result:
        translated_input = self._translate(input)
        result = self._get_talent_in_list(translated_input, talent_slugs)
      if not result:
        return input
      i = talent_slugs.index(result)
      return self.state.details_data.all_talents[i].get('name')
    except Exception as e:
      self.logger.log_only('error', f'error: {e}')
      return input
  
  def _normalize(self, input: str) -> str:
    input = re.sub(r'[\U00010000-\U0010ffff]', '', input, flags=re.UNICODE)
    input = re.sub(r'[\u2600-\u27BF\u2300-\u23FF\u2700-\u27BF]', '', input)
    input = re.sub(r'\b\d+\b', '', input)
    input = unicodedata.normalize('NFKD', input).encode('ascii', 'ignore').decode()
    return str_to_slug(input)

  def _get_talent_in_list(self, user_input: str, talents: list[str], threshold: float = 0.6) -> str|None:
    normalized_input = self._normalize(user_input)
    if normalized_input in talents:
      return normalized_input
    close = get_close_matches(normalized_input, talents, n=1, cutoff=threshold)
    if close:
      return close[0]
    words = normalized_input.split('-')
    ngrams = ['-'.join(words[i:i+size]) for size in range(len(words), 0, -1) for i in range(len(words) - size + 1)]
    for ngram in ngrams:
      close = get_close_matches(ngram, talents, n=1, cutoff=threshold)
      if close:
        return close[0]
    return None

  #    get current climb (from spire)
  def _get_current_climb(self) -> int:
    now = self.date
    for climb in self.state.details_data.spire.get('climbs'):
      start = datetime.strptime(climb['start_date'], "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
      end = datetime.strptime(climb['end_date'], "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
      if start <= now <= end:
        return climb.get('number')
    return None
  
  #    translate
  def _translate(self, key, langcode: Optional[str] = None) -> str:
    if langcode is None:
      langcode = self.ui.langcode
    return self.bot.language.translate_from_key(text_to_translate=key, lang=langcode)