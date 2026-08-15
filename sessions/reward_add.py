from ui.base_ui import BaseUiData
from states.reward import RewardState

from ui.reward.views import SelectorView, ValidationView
from ui.reward.modals import QuantityModal
from ui.reward.common import RewardCommon

from utils.str_utils import slug_to_str, str_to_slug, str_to_int, int_to_str
from utils.misc_utils import nick


class RewardAddSession:
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
    self.state.set_reward('times', 1)

  # Session entry point
  async def start(self):
    try:
      if str_to_slug(self.state.level_name) == self._translate('help'):
        return await self._return_help()
      check = self._check_level_name()
      if check:
        return await self._return_error(error='not found')
      self.state.all_levels = await self.bot.back_requests.call('getAllLevels')
      if 'error' in self.state.all_levels:
        return await self._return_error(error='request error')
      self.state.level = next((l for l in self.state.all_levels if (slug_to_str(self.state.level_name) in l.get('name') or self.state.level_name == l.get('name_slug'))), None)
      if not self.state.level:
        return await self._return_error(error='not found')
      self.state.level_name = self.state.level.get('name').get(self.ui.langcode, self.state.level.get('name').get('en'))
      await self.advance()
    except Exception as e:
      self.logger.log_only('error', f'[REWARD ADD] Error : {e}')

  # Return help endpoint
  async def _return_help(self):
    self.ui.response = self.bot.message.get_help(whichone='reward add', lang=self.ui.langcode)
    await self.ui.send()
    self.logger.ok_log('reward add', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)
  
  # Error endpoint
  async def _return_error(self, error: str):
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'not found':
        self.logger.log_only('debug', f'[REWARD ADD] {self.state.level_name} not found')
        description += f'{self.error_msg.get('reward').get('part1')}{self.state.level_name}{self.error_msg.get('reward').get('part2')}'
      case 'not an int':
        self.logger.log_only('debug', f'[REWARD ADD] {self.state.selected.get('quantity')} is not an integer')
        description += f'{self.error_msg.get('reward').get('not int1')}{self.state.selected.get('quantity')}{self.error_msg.get('reward').get('not int2')}'
      case 'request error':
        self.logger.log_only('error', f'[REWARD ADD] Error while requesting backend')
        description += self.error_msg.get('generic')
    self.ui.response = {'description': description, 'color': self.bot.message.get_message('error').get('color')}
    await self.ui.send()
    self.logger.nok_log('reward add', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)

  # Check level name helper
  def _check_level_name(self) -> bool:
    found = any((slug_to_str(self.state.level_name) == choice.name or str_to_slug(self.state.level_name) == choice.value)
                for choices in self.cog.level_choices.values()
                for choice in choices)
    if found:
      return False
    return True
  
  # Advance -> Flow manager entry point
  async def advance(self):
    if self.state.selection: # pre-check : set selection
      match self.state.step: 
        case 'type':
          split_selection = self.state.selection.split()
          self.state.set_reward('type', split_selection[1])
          self.state.set_reward('quality', split_selection[0])
        case 'quality'|'item':
          self.state.set_reward(self.state.step, self.state.selection)
        case 'quantity':
          self.state.set_reward('quantity', str_to_int(self.state.selection))
        case 'validation':
          self.state.set_reward('times', int(self.state.selection))
      self.logger.log_only('debug', f'[REWARD ADD] Selected: {self.state.selected}')
    self.state.next_step()
    match self.state.step:
      case 'type'|'quality'|'item':
        await self._render_selector_view()
      case 'quantity':
        await self._render_modal()
      case 'validation':
        await self._render_validation_view()
      case 'finish':
        await self._render_finish()
  
  # Render ui
  #    selector_view
  async def _render_selector_view(self):
    self.logger.log_only('debug', f'[REWARD ADD] Render {self.state.step} view')
    await self.ui.clear()
    match self.state.step:
      case 'type':
        self._build_type()
      case 'quality':
        self._build_quality()
      case 'item':
        self._build_item()
    self.ui.view = SelectorView(self)
    await self.ui.send()
  
  #    quantity (input modal)
  async def _render_modal(self):
    self.logger.log_only('debug', '[REWARD ADD] Render quantity modal')
    await self.ui.clear()
    self._build_quantity()
    self.ui.modal = QuantityModal(self)
    await self.ui.send()

  #    validation (ok/cancel view)
  async def _render_validation_view(self):
    self.logger.log_only('debug', '[REWARD ADD] Render validation view')
    await self.ui.clear()
    self._build_validation()
    self.ui.view = ValidationView(self)
    await self.ui.send()

  #    cancel endpoint
  async def _render_cancel(self):
    self.logger.log_only('debug', f'[REWARD ADD] Reward canceled by {self.state.user}')
    await self.ui.clear()
    description = f'## {self.state.level_name} ##\n{self.return_msg.get('cancel message')}'
    self.ui.response = {'description': description, 'color': self.bot.message.get_message('error').get('color')}
    await self.ui.send()
    self.logger.ok_log('reward add', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)

  #    finish endpoint (final step : add reward to BDD and send reward list for the selected level)
  async def _render_finish(self):
    await self.ui.clear()
    self.state.level = await self._post_reward()
    if 'error' in self.state.level:
      return await self._return_error(error='request error')
    common = RewardCommon(self)
    reward_list, chart_img = common.display_rewards()
    description = (
      f'## {self.state.level_name} ##\n{self.return_msg.get('return1')}'
      f'{self._build_return_message()}{self.return_msg.get('return2')}{reward_list}'
    )
    self.ui.response = {'description': description, 'color': self.bot.message.get_message('reward').get('color'), 'image': True}
    self.ui.files = [chart_img]
    await self.ui.send()
    self.logger.ok_log('reward add', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)

  # Timeout handler
  async def handle_timeout(self, whichone: str):
    self.logger.log_only('debug', f'[REWARD ADD] {whichone} timeout')
    await self.ui.clear()
    self.ui.timeout_message = True
    await self.ui.send()
    self.logger.timeout_log('reward add', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)

  # Modal validation handler
  async def handle_modal_submit(self, value: str):
    try:
      int_value = str_to_int(value)
      await self.ui.clear()
      if int_value:
        self.state.set_reward('quantity', int_value)
        return await self.advance()
      self.state.set_reward('quantity', value)
      return await self._return_error('not an int')
    except Exception as e:
      self.bot.logger.log_only('warning', f'[REWARD ADD] Error on modal submit : {e}')

  # View/modal builders
  #    type choices/content/placeholder
  def _build_type(self):
    self.state.choices = []
    for i in range(len(self.state.reward_choices())):
      type_choice = self.state.reward_choices()[i]
      quality_choices = type_choice.get('choices')[0]
      for j in range(len(quality_choices.get('choices'))):
        quality_choice = quality_choices.get('choices')[j]
        choice = f'{quality_choice.get('name')} {type_choice.get('name')}'
        self.state.choices.append({'label': self._translate(choice), 'value': choice, 'icon': quality_choice.get('icon')})
    self.ui.content = f'\n## {self.state.level_name} ## \n{self.return_msg.get('type content')}'
    self.state.placeholder = self.return_msg.get('type placeholder')

  #    quality choices/content/placeholder
  def _build_quality(self):
    quality_choices = self.state.current_choice_node('Quality')
    self.state.choices = sorted([{'label': self._translate(q.get('name')), 'value': q.get('name'), 'icon': q.get('icon'), 'grade': q.get('grade')} for q in quality_choices],
                                key=lambda x:x.get('grade'))
    self.ui.content = f'\n## {self.state.level_name} ## \n{self.return_msg.get('quality content')}{self._translate(self.state.selected.get('type'))}"'
    self.state.placeholder = self.return_msg.get('quality placeholder')

  #    item choices/content/placeholder
  def _build_item(self):
    item_choices = self.state.current_choice_node('Item')
    self.state.choices = sorted([{'label': self._translate(i.get('name')), 'value': i.get('name'), 'icon': None} for i in item_choices],
                                key=lambda x:x.get('label'))
    self.ui.content = f'\n## {self.state.level_name} ## \n{self.return_msg.get('item content')}'
    self.state.placeholder = self.return_msg.get('item placeholder')
    self.state.previous_label = self.return_msg.get('previous')
    self.state.next_label = self.return_msg.get('next')

  #    quantity title/input label
  def _build_quantity(self):
    self.ui.title = f'{self.state.level_name}'
    self.state.modal_label = self.return_msg.get('quantity label')
    self.state.placeholder = self.return_msg.get('quantity placeholder')

  #    validation choices/content
  def _build_validation(self):
    self.state.choices = [{'label': str(i), 'value': i, 'icon': None} for i in range(1, 11)]
    content = (
      f'{self.return_msg.get('validation1')}'
      f'{self._build_return_message()}'
      f'{self.return_msg.get('validation3')}'
    )
    self.ui.content = f'\n## {self.state.level_name} ## \n{content}'
    self.state.ok_label = self.return_msg.get('ok')
    self.state.cancel_label = self.return_msg.get('cancel')

  #    return message
  def _build_return_message(self):
    return_message = (
      f'{self.state.selected.get('times')}'
      f'{self.return_msg.get(f'validation2{'S' if self.state.selected.get('times') == 1 else 'P'}')}'
    )
    if 'quantity' in self.state.selected.keys():
      return_message += str(int_to_str(self.state.selected.get('quantity')))
      if 'quality' in self.state.selected.keys():
        return_message += f' {self._translate(f'{self.state.selected.get('quality')} {self.state.selected.get('type')}')}'
      else:
        return_message += f' {self._translate(self.state.selected.get('type'))}'
    else:
      return_message += self._translate(f'{self.state.selected.get('quality')} {self.state.selected.get('item')}')
    return return_message
  
  # Post level helper
  async def _post_reward(self):
    self.logger.log_only('debug', f'[REWARD ADD] Post reward')
    payload = {}
    payload['reward'] = self.state.selected
    payload['level'] = self.state.level.get('name_slug')
    return await self.bot.back_requests.call('addReward', [payload])

  # Translate helper
  def _translate(self, key) -> str:
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)