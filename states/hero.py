from dataclasses import dataclass, field


@dataclass(slots=True)
class HeroState():
  hero: str = None
  hero_dict: dict = field(default_factory=dict)
  pet_dict: dict = field(default_factory=dict)
  pet_active_talent: dict = field(default_factory=dict)