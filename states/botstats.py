from dataclasses import dataclass, field
  

@dataclass(slots=True)
class BotStatsState():
  talents: list = field(default_factory=list)
  heroes: list = field(default_factory=list)
  pets: list = field(default_factory=list)