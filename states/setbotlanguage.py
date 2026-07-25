from dataclasses import dataclass, field
from typing import Optional
  

@dataclass(slots=True)
class SetbotlanguageState():
  langcode: Optional[str] = None
  channel_id: Optional[int] = None
  language_set: dict = field(default_factory=dict)