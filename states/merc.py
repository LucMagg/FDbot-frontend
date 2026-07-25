from dataclasses import dataclass, field


@dataclass(slots=True)
class MercState():
  user: str = None
  user_id: str = None
  guild_id: str = None
  guild_name: str = None
  found_hero: dict = field(default_factory=dict)
  heroes: list[dict] = field(default_factory=list[dict])
  merc: dict = field(default_factory=dict)
  merc_list: list[dict] = field(default_factory=list[dict])
  user_list: list[dict] = field(default_factory=list[dict])
  
  # Clean merc helpers
  def clean_merc_values(self) -> dict:
    for talent_key in ('a2_talent', 'a3_talent', 'a4_talent'):
      if self.merc.get(talent_key):
        self.merc['ascend'] = talent_key.split('_')[0].capitalize()
    if self.merc.get('ascend'):
      match self.merc.get('ascend'):
        case 'A3':
          self.merc['a2_talent'] = True
        case 'A4':
          self.merc['a2_talent'] = True
          self.merc['a3_talent'] = True
    if self.merc.get('pet_talent'):
      self.merc['pet'] = True
    if self.merc.get('pet') and not self.found_hero.get('pet'):
      return {'error': 'no pet found'}
    if self.merc.get('ascend') == 'A4' and self.found_hero.get('ascend_max') != 'A4':
      return {'error': 'no A4'}
    return {k: self._normalize(v) for k, v in self.merc.items() if v is not None}

  def _normalize(self, v) -> bool|str:
    if isinstance(v, str):
      if v.lower() == 'true':
        return True
      if v.lower() == 'false':
        return False
    return v