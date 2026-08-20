import discord
from typing import Optional

from ui.base_ui import BaseUiData
from states.level import LevelState

from ui.level.views import RootView, RewardView
from ui.level.modals import NameLocalizationsModal

from utils.misc_utils import nick


class LevelSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger
    self.all_languages_levels = self.cog.all_languages_levels

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = LevelState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('level').get(self.ui.langcode)

    self.other_available_languages = [{'lang':'fr', 'label': 'Entrez le nom en français'}]
    self.state.name['en'] = cog_data.get('name_in_english')
    self.state.standard_energy_cost = cog_data.get('standard_energy_cost')
    self.state.coop_energy_cost = cog_data.get('coop_energy_cost')
    self.state.reward_types = self.cog.reward_types
    self.state.submit_label = self.return_msg.get('submit')
    self.state.next_label = self.return_msg.get('next')

  # Session entry point  
  async def start(self):
    try:
      if not await self._allowed_user():
        return
      if not await self._process_level_response():
        return
      await self.render_modal()
    except Exception as e:
      self.logger.session_exception('Level', e)

  # First step : level name translations modal
  async def render_modal(self):
    self.logger.log('debug', '[LEVEL] Render NameLocalizations modal')
    self.ui.title = self.return_msg.get('translations')
    self.ui.modal = NameLocalizationsModal(self, fields=self.other_available_languages)
    await self.ui.send()
  
  async def handle_modal_submit(self, interaction: discord.Interaction, data: dict):
    self.logger.log('debug', '[LEVEL] NameLocalizations modal submit')
    await self.ui.clear()
    await self.ui.set_interaction(interaction=interaction)
    for index, d in enumerate(data):
      self.state.name[self.other_available_languages[index].get('lang')] = d
    exists = self._translation_already_exists()
    if exists:
      await self._return_error('already exists', lang=exists)
      return
    self.logger.log('debug', f'[LEVEL] Names : {self.state.name}')
    await self.render_root()

  # Second step : root view
  async def render_root(self):
    self.logger.log('debug', '[LEVEL] Render Root view')
    if self.ui.view:
      self.ui.view.stop()
    self.ui.content = self.return_msg.get('reward types')
    self.ui.view = RootView(self)
    await self.ui.send()

  async def validate_root_selection(self):
    self.logger.log('debug', '[LEVEL] Root view validation')
    self.logger.log('debug', f'[LEVEL] selected_rewards {self.state.selected_rewards}')
    action = self.state.validate_root()
    if action == 'invalid':
      return
    if action == 'finish':
      await self.finish()
    else:
      await self.render_reward()

  # Third step : reward view
  async def render_reward(self):
    self.logger.log('debug', '[LEVEL] Render Reward view')
    if self.ui.view:
      self.ui.view.stop()
    reward_node = self.state.get_reward_node()
    reward_name = reward_node.get('name').get(self.ui.langcode).capitalize()
    group_node = self.state.get_current_group_node()
    group_name = group_node.get('name').get(self.ui.langcode).lower()
    self.ui.content = f'{self.return_msg.get('choice part1')} {group_name} {self.return_msg.get('choice part2')}{reward_name}"'
    self.ui.view = RewardView(self)
    await self.ui.send()

  async def validate_reward_selection(self):
    self.logger.log('debug', '[LEVEL] Reward view validation')
    self.logger.log('debug', f'[LEVEL] selected_rewards {self.state.selected_rewards} | selections {self.state.selections}')
    action = self.state.advance_reward_flow()
    if action == 'finish':
      await self.finish()
    else:
      await self.render_reward()
  
  # Final step : build/add level to BDD and send confirmation
  async def finish(self):
    self.logger.log('debug', '[LEVEL] Reward final message')
    await self.ui.clear()
    level = await self._add_level()
    if not level:
      self.logger.log('error', '[LEVEL] Error while sending level')
      self.ui.generic_error_message = True
    else:
      self.logger.log('debug', '[LEVEL] New level created')
      self.ui.response = {'description': f'{self.return_msg.get('final part1')}{self.state.name.get('self.ui.langcode')}{self.return_msg.get('final part2')}', 'color': 'default'}
    await self.ui.send()
    self.logger.ok_log('level', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)

  # Timeout handler
  async def handle_timeout(self, whichone: str, timeout: int = 180):
    self.logger.log('debug', f'[LEVEL] {whichone} timeout')
    await self.ui.clear()
    self.ui.timeout = timeout
    self.ui.timeout_message = True
    await self.ui.send()
    self.logger.timeout_log('level', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)

  # Error builder
  async def _return_error(self, error: str, author: str = '', lang: str = 'en'):
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'not allowed user':
        self.logger.log('debug', f'[LEVEL] User {author} not allowed to create a level')
        description += self.error_msg.get('level').get('private')
      case 'already exists':
        self.logger.log('debug', f'[LEVEL] Level name already exists in language [{lang}]')
        description += f'{self.error_msg.get('level').get('part1')}{self.state.name[lang]}{self.error_msg.get('level').get('part2')}'
      case 'no energy':
        self.logger.log('debug', '[LEVEL] Missing parameters')
        description += self.error_msg.get('level').get('no_energy')
    self.ui.response = {'description': description, 'color': self.bot.message.get_message('error').get('color')}
    await self.ui.send()
    self.logger.nok_log('level', self.ui.interaction)
    self.bot.session_manager.delete(self.ui.interaction)

  # Pre-check helpers
  async def _allowed_user(self) -> bool:
    author = str(self.ui.interaction.user)
    if 'spirou' in author or 'prep' in author:
      return True
    await self._return_error('not allowed user', author=nick(self.ui.interaction.user))
    return False

  async def _process_level_response(self) -> bool:
    if self.state.name.get('en') in [c.name for c in self.cog.choices.get('en')]:
      await self._return_error('already exists', lang='en')
      return False
    if not self.state.standard_energy_cost and not self.state.coop_energy_cost:
      await self._return_error('no energy')
      return False
    return True

  # Modal check helper
  def _translation_already_exists(self) -> Optional[str]:
    for k, v in self.state.name.items():
      for choice in self.all_languages_levels.get(k, []):
        if choice.name == v.strip():
          return k
    return None
  
  # Build level helper
  async def _add_level(self) -> bool:
    rewards = self.state.build_global_selected_rewards()
    self.logger.log('debug', f'[LEVEL] Level final data : {rewards}')
    gear = next((g for g in rewards if g.get('name').get('en') == 'gear'), None)
    if gear: # gear special case
      gear_choices = await self._resolve_gear(gear.get('choices'))
      if not gear_choices:
        return False
      gear['choices'] = gear_choices
    payload = {
      'name': self.state.name,
      'standard_energy_cost': self.state.standard_energy_cost,
      'coop_energy_cost': self.state.coop_energy_cost,
      'reward_choices': rewards
    }
    post_level = await self.bot.back_requests.call('addLevel', [payload])
    return bool(post_level)
  
  async def _resolve_gear(self, choices: list[dict]) -> bool:
    hero_types_group = next((c for c in choices if c.get('name').get('en') == 'Hero Types'), None)
    positions_group = next((c for c in choices if c.get('name').get('en') == 'Gear Position'), None)
    quality_group = next((c for c in choices if c.get('name').get('en') == 'Quality'), None)
    if not hero_types_group or not positions_group:
      return False
    hero_types = hero_types_group.get('choices', [])
    gear_positions = positions_group.get('choices', [])
    types = ','.join(t['name']['en'] for t in hero_types)
    positions = ','.join(p['name']['en'] for p in gear_positions)
    items = await self.bot.back_requests.call('getUniqueGearByTypeAndPosition', [types, positions])
    if not items:
      return False
    items.sort(key=lambda i: i.get('name'))
    item_choices = [
      {'name': {'en': item['name'], 'fr': self.bot.language.translate_from_key(text_to_translate=item['name'], lang='fr')}, 'icon': '', 'grade': i}
      for i, item in enumerate(items) if item['name'] != ''
    ]
    return [
      quality_group,
      {
        'name': {'en': 'Item', 'fr': 'Objet'},
        'icon': '',
        'grade': 3,
        'choices': item_choices,
      },
    ]