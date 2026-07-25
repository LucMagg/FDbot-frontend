from dataclasses import dataclass, field
from typing import Optional
  

@dataclass(slots=True)
class RewardState():
  # base
  user: Optional[str] = None
  level_name: Optional[str] = None
  all_levels: list[dict] = field(default_factory=list)
  level: dict = field(default_factory=dict)
  # nav
  step: str = 'init' # init -> [type, item, quality, quantity] -> validation
  selected: dict = field(default_factory=dict)
  times: int = 1
  # selector choices
  choices: list[dict] = field(default_factory=list)
  placeholder: Optional[str] = None
  selection: Optional[str] = None
  page: Optional[int] = 0
  # modal
  modal_label: Optional[str] = None
  # button labels
  ok_label: Optional[str] = None
  cancel_label: Optional[str] = None
  previous_label: Optional[str] = None
  next_label: Optional[str] = None

  def set_reward(self, key: str, value):
    self.selected[key] = value
    self.selection = None

  def reward_choices(self):
    return sorted(self.level.get('reward_choices'), key=lambda x:x['grade'])

  def has_multiple_types(self) -> bool:
    return len(self.reward_choices()) > 1

  def current_type_node(self):
    return next((c for c in self.reward_choices() if c.get('name') == self.selected.get('type')), None)
  
  def current_choice_node(self, whichone: str):
    choice_node = next((c for c in self.current_type_node().get('choices') if c.get('name') == whichone), None)
    return sorted(choice_node.get('choices'), key=lambda x:x['grade'])

  def has_quality(self) -> bool:
    node = self.current_type_node()
    if not node or not node.get('choices'):
      return False
    return any(c.get('name').lower() == 'quality' for c in node.get('choices'))

  def has_item(self) -> bool:
    node = self.current_type_node()
    if not node or not node.get('choices'):
      return False
    return any(c.get('name').lower() == 'item' for c in node.get('choices'))

  def has_quantity(self) -> bool:
    node = self.current_type_node()
    return node and node.get('has_quantity')

  def is_quantity_only(self) -> bool:
    return (
      len(self.reward_choices()) == 1
      and not self.reward_choices()[0].get('choices')
      and self.reward_choices()[0].get('has_quantity')
    )
  
  def next_step(self):
    match self.step:
      case 'init':
        if self.is_quantity_only():
          self.set_reward('type', self.reward_choices()[0].get('name'))
          self.step = 'quantity'
          return
        if self.has_multiple_types():
          self.step = 'type'
          return
        self.set_reward('type', self.reward_choices()[0].get('name'))
        if self.has_quality():
          self.step = 'quality'
        elif self.has_quantity():
          self.step = 'quantity'
        else:
          self.step = 'validation'
        return
      case 'type':
        if self.selected.get('type') == 'gear':
          self.step = 'item'
          return
        self.step = 'quantity'
        return
      case 'quality':
        if self.has_item():
          self.step = 'item'
        elif self.has_quantity():
          self.step = 'quantity'
        else:
          self.step = 'validation'
        return
      case 'item':
        self.step = 'validation'
        return
      case 'quantity':
        self.step = 'validation'
        return
      case 'validation':
        self.step = 'finish'