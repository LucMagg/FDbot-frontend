from dataclasses import dataclass, field, fields, asdict
from typing import Optional

import discord


@dataclass(slots=True)
class SpireData():
  username: Optional[str] = None
  user_id: Optional[int] = None
  guild: Optional[str] = None
  date: Optional[str] = None
  spire: Optional[int] = None
  climb: Optional[int] = None
  tier: Optional[str] = None
  floors: Optional[int] = None
  loss: Optional[int] = None
  turns: Optional[int] = None
  bonus: Optional[int] = None
  score: Optional[int] = None
  all_tiers = ['Platinum', 'Gold', 'Silver', 'Bronze', 'Hero', 'Adventurer']
  all_guilds: list[str] = field(default_factory=list)  

  def from_dict(self, data: dict) -> None:
    valid_keys = {f.name for f in fields(self)}
    for k, v in data.items():
      if k in valid_keys:
        try:
          setattr(self, k, int(v))
        except:
          setattr(self, k, v)
  
  def to_dict(self) -> dict:
    return {k: v for k, v in asdict(self).items() if k not in ['all_guilds', 'all_tiers']}
  
  def is_done(self) -> bool:
    if any(getattr(self, f.name) is None for f in fields(self)):
      return False
    return self.is_guild_valid() and self.is_tier_valid() and self.is_climb_valid() and self.is_score_valid()
  
  def is_guild_valid(self) -> bool:
    if not self.all_guilds or not self.guild:
      return False
    if not self.guild.lower() in [g.lower() for g in self.all_guilds]:
      return False
    self.guild = next((g for g in self.all_guilds if g.lower() == self.guild.lower()), None)
    return True
  
  def is_tier_valid(self) -> bool:
    if not self.tier:
      return False
    if not self.tier.lower() in [t.lower() for t in self.all_tiers]:
      return False
    self.tier = next((t for t in self.all_tiers if t.lower() == self.tier.lower()), None)
    return True
  
  def is_climb_valid(self) -> bool:
    return self.climb and self.climb in range(1, 5)
    
  def is_score_valid(self) -> bool:
    return self.is_floors_valid() and self.is_loss_valid() and self.is_turns_valid() and self.is_bonus_valid()
  
  def is_floors_valid(self) -> bool:
    return isinstance(self.floors, int) and self.floors in range(0, 15)
  
  def is_loss_valid(self) -> bool:
    return isinstance(self.loss, int) and self.loss >= 0
  
  def is_turns_valid(self) -> bool:
    return isinstance(self.turns, int) and self.turns >= 31
  
  def is_bonus_valid(self) -> bool:
    return isinstance(self.bonus, int) and self.bonus in range(0, 85)
  
  def calculate_score(self) -> int:
    return self.floors * 50000 - self.loss * 1000 - self.turns * 100 + self.bonus * 250

@dataclass(slots=True)
class SpireState():
  # file
  screenshot: discord.Attachment = None
  file_name: Optional[str] = None
  file_path: Optional[str] = None
  # spire data
  spire_data: SpireData = field(default_factory=SpireData)
  # nav
  step: str = 'main' # main -> [guild -> [create, exists], tier, climb, score -> score error] -> finish
  selection: Optional[str] = None
  page: Optional[int] = 0
  validate: bool = False
  inputs: dict[str, str] = None
  # selector choices
  choices: list[dict] = field(default_factory=list)
  placeholder: Optional[str] = None
  # modal
  modal_label: Optional[str] = None
  modal_inputs: list[dict] = field(default_factory=list)
  # button labels
  guild_label: Optional[str] = None
  tier_label: Optional[str] = None
  climb_label: Optional[str] = None
  score_label: Optional[str] = None
  validation_label: Optional[str] = None
  previous_label: Optional[str] = None
  next_label: Optional[str] = None
  yes_label: Optional[str] = None
  no_label: Optional[str] = None
  ok_label: Optional[str] = None

  def set_item(self, key: str, value):
    try:
      setattr(self.spire_data, key, int(value))
    except:
      setattr(self.spire_data, key, value)
  
  def clear_nav(self):
    self.selection = None
    self.page = 0
    self.validate = False
    self.inputs = None
  
  def to_dict(self) -> dict:
    return {
      'image_url': self.file_path,
      **self.spire_data.to_dict()
    }