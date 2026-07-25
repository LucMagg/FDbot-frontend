from dataclasses import dataclass, field


@dataclass(slots=True)
class ClasseState():
  classe: str = None
  heroes: list = field(default_factory=list)
  pets: list = field(default_factory=list)