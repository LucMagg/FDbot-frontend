from dataclasses import dataclass, field


@dataclass(slots=True)
class ExclusiveState():
  event: str = None
  heroes: list = field(default_factory=list)
  pets: list = field(default_factory=list)
  exclusives: list = field(default_factory=list)
  embed_color: str = None