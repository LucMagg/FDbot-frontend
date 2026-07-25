from dataclasses import dataclass, field
from typing import Optional
  

@dataclass(slots=True)
class Set_trapState():
  trap_id: Optional[str] = None
  guild_id: Optional[int] = None
  trap_set: dict = field(default_factory=dict)