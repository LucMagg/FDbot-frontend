import math

from ui.base_ui import BaseUiData
from states.xp import XpState

from utils.misc_utils import stars

class XpSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = XpState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode).get('xp')
    self.return_msg = self.bot.message.get_message('xp').get(self.ui.langcode)
    
    self.state.stars = cog_data.get('stars')
    self.state.current_ascend = cog_data.get('current_ascend')
    self.state.current_level = cog_data.get('current_level')
    self.state.target_ascend = cog_data.get('target_ascend')
    self.state.target_level = cog_data.get('target_level')
    self.state.xp_data = self.bot.static_data.xp_data
    self.state.thresholds = self.bot.static_data.xp_thresholds

  # Session entry point
  async def start(self):
    try:
      self.ui.wait_message = True
      await self.ui.send()
      await self.ui.clear()
      self.ui.response = await self._get_response()
      await self.ui.send()
    except Exception as e:
      self.logger.session_exception('Xp', e)

  # Get command response
  async def _get_response(self) -> dict:
    check_for_errors = self.state.check_for_errors()
    if check_for_errors:
      return self._return_error(error=check_for_errors)
    return {'description': self._build_description(), 'color': self.bot.message.get_message('xp').get('color')}
  
  # Error builder
  def _return_error(self, error: str) -> dict:
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'input error current':
        self.logger.log('debug', f'[XP] Current input error : {self.state.current_ascend} lvl {self.state.current_level}')
        description += (
          f'{self.error_msg.get('start')}{self.state.stars}{self.error_msg.get('input1')}'
          f'{self.state.current_ascend}{self.error_msg.get('input2')}{self.state.current_level}{self.error_msg.get('input3')}'
        )
      case 'input error target':
        self.logger.log('debug', f'[XP] Target input error : {self.state.target_ascend} lvl {self.state.target_level}')
        description += (
          f'{self.error_msg.get('start')}{self.state.stars}{self.error_msg.get('input1')}'
          f'{self.state.target_ascend}{self.error_msg.get('input2')}{self.state.target_level}{self.error_msg.get('input3')}'
        )
      case 'same level':
        description += self.error_msg.get('same level')
      case 'ascend downgrade':
        description += f'{self.error_msg.get('start')}{self.error_msg.get('ascend down')}'
      case 'level downgrade':
        description += f'{self.error_msg.get('start')}{self.error_msg.get('level down')}.'
      case 'incorrect path':
        description += (
          f'{self.error_msg.get('start')}{self.error_msg.get('path1')}{self.state.current_ascend}{self.error_msg.get('path2')}'
          f'{self.state.current_level}{self.error_msg.get('path3')}{self.state.target_ascend}{self.error_msg.get('path2')}'
          f'{self.state.target_level}{self.error_msg.get('path4')}{self.error_msg.get('path2')}{math.ceil(self.state.current_level / 2)}'
        )
    description += f'\n{self.error_msg.get('end')}'
    return {'description': description, 'color': self.bot.message.get_message('error').get('color')}
  
  # Description builder
  def _build_description(self) -> str:
    steps = self.state.calculate_steps()
    return (
      f'## {stars(self.state.stars)} ##\n'
      f'{self._str_from_steps(steps)}'
    )

  # Steps helpers
  #    str from steps (entry point)
  def _str_from_steps(self, steps: list[dict]) -> str:
    total_potions = sum(step['potions'] for step in steps)
    total_gold = sum(step['gold'] or 0 for step in steps)
    total_heroic = sum(step['heroic'] or 0 for step in steps)
    base = self._build_base(total_potions, total_gold, total_heroic)
    if len(steps) == 1:
      return f'{base}{self.return_msg.get('no steps')}'
    return f'{base}{self.return_msg.get('steps')}{'\n'.join(self._build_details(steps))}'
  
  #    base builder
  def _build_base(self, total_potions: int, total_gold: int, total_heroic: int) -> str:
    base = f'{self.return_msg.get('part1')}{total_potions}{self.return_msg.get('part2')}' 
    if total_gold and total_heroic:
      base += (
        f'{self.return_msg.get('comma')}{total_gold}{self.return_msg.get('gold')}'
        f'{self.return_msg.get('and')}{total_heroic}{self.return_msg.get('heroic xp')}'
      )
    elif total_gold:
      base += f'{self.return_msg.get('and')}{total_gold}{self.return_msg.get('gold')}'
    base += (
      f'{self.return_msg.get('part3')}{self.state.stars}{self.return_msg.get('part4')}'
      f'{self.state.current_ascend}{self.return_msg.get('level')}{self.state.current_level}{self.return_msg.get('to')}'
      f'{self.state.target_ascend}{self.return_msg.get('level')}{self.state.target_level}'
    )
    return base
  
  #    details builder
  def _build_details(self, steps: list[dict]) -> list[str]:
    details = []
    for step in steps:
      if step.get('skip'):
        details.append(f'{self.return_msg.get('skip')}{self._ascend_line(step)}')
      else:
        if step.get('gold'):
          details.append(f'{self.return_msg.get('ascend')}{self._ascend_line(step)}')
        else:
          details.append(self._potion_line(step))
    return details

  #    ascend line helper
  def _ascend_line(self, step: dict) -> str:
    result = f'{step.get('ascend')}{self.return_msg.get('for')}{step.get('gold')}{self.return_msg.get('gold')}'
    if step.get('heroic') > 0:
      result += f'{self.return_msg.get('and')}{step.get('heroic')}{self.return_msg.get('heroic xp')}'
    return result
  
  #    potion line helper
  def _potion_line(self, step: dict) -> str:
    return f'{self.return_msg.get('xp1')}{step.get('potions')}{self.return_msg.get('xp2')}{self.return_msg.get('level')}{step.get('level')}'