from dataclasses import dataclass, field
from typing import Optional
import discord


@dataclass(slots=True)
class SpireData:
  spire: Optional[dict] = None
  climb: Optional[int] = None
  selected_map: Optional[dict] = None
  map_url: Optional[str] = None
  hero_bonus: dict = field(default_factory=dict)
  monster_bonus: dict = field(default_factory=dict)
  talents: dict = field(default_factory=dict)
  all_maps: list[dict] = field(default_factory=list[dict])
  all_tiers: list = field(default_factory=lambda: ['Platinum', 'Gold', 'Silver', 'Bronze', 'Hero', 'Adventurer'])
  all_talents: list[dict] = field(default_factory=list[dict])

  def from_climb_details(self, climb_details: dict, all_maps: list) -> None:
    if 'map' in climb_details:
      self.selected_map = next((m for m in all_maps if m.get('name') == climb_details['map'].get('name')), None)
      if self.selected_map:
        self.selected_map['water_or_lava'] = climb_details['map'].get('water_or_lava')
    self.hero_bonus = climb_details.get('hero_bonus', {})
    self.monster_bonus = climb_details.get('monster_bonus', {})
    self.talents = climb_details.get('talents', {})

  def is_map_valid(self) -> bool:
    return self.selected_map is not None

  def is_hero_bonus_valid(self) -> bool:
    return bool(self.hero_bonus)

  def is_monster_bonus_valid(self) -> bool:
    result = bool(self.monster_bonus)
    if self.climb == 2:
      result = False
    return result

  def is_talents_valid(self) -> bool:
    return bool(self.talents)

  def has_any_detail(self) -> bool:
    return self.is_map_valid() or self.is_hero_bonus_valid() or self.is_monster_bonus_valid() or self.is_talents_valid()

  def to_dict(self) -> dict:
    result = {}
    if self.selected_map:
      result['map'] = {'name': self.selected_map.get('name'), 'water_or_lava': self.selected_map.get('water_or_lava')}
    result['hero_bonus'] = self.hero_bonus
    result['monster_bonus'] = self.monster_bonus
    result['talents'] = self.talents
    return result


@dataclass(slots=True)
class SpireState:
  # data
  details_data: SpireData = field(default_factory=SpireData)
  max_talents_floor = 13
  # nav
  step: str = 'main' # main -> [map -> [water_or_lava], hero_bonus -> [hero_bonus_validation], monster_bonus -> [monster_bonus_validation], bracket -> [talents, talents_between] ] -> finish
  validate: bool = False
  inputs: Optional[dict] = None
  selected_tier: Optional[str] = None
  talents_step: int = 1
  # selector
  choices: list = field(default_factory=list)
  placeholder: Optional[str] = None
  selection: Optional[str] = None
  page: Optional[int] = 0
  # modal
  modal_inputs: list = field(default_factory=list)
  # button labels
  main_buttons: list = field(default_factory=lambda: ['map', 'hero_bonus', 'monster_bonus', 'talents'])
  map_label: Optional[str] = None
  hero_bonus_label: Optional[str] = None
  monster_bonus_label: Optional[str] = None
  talents_label: Optional[str] = None
  cancel_label: Optional[str] = None
  validate_label: Optional[str] = None
  change_label: Optional[str] = None
  finish_label: Optional[str] = None
  yes_label: Optional[str] = None
  no_label: Optional[str] = None
  next_label: Optional[str] = None
  previous_label: Optional[str] = None
  water_label: Optional[str] = None
  lava_label: Optional[str] = None
  continue_label: Optional[str] = None
  ok_label: Optional[str] = None

  def clear_nav(self):
    self.validate = False
    self.inputs = None
    self.selection = None