from dataclasses import dataclass, field


@dataclass(slots=True)
class ItemState():
  item: str = None
  parsed_item: dict = field(default_factory=dict)
  heroes: list[dict] = field(default_factory=list[dict])
  levels: list[dict] = field(default_factory=list[dict])