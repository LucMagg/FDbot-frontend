from dataclasses import dataclass, field


@dataclass(slots=True)
class TalentState():
  talent: str = None
  talent_dict: dict = field(default_factory=dict)
  heroes: list[dict] = field(default_factory=list[dict])
  pets: list[dict] = field(default_factory=list[dict])