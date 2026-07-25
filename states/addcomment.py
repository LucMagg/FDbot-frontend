from dataclasses import dataclass
from typing import Optional
  

@dataclass(slots=True)
class AddCommentState():
  hero_or_pet: str = ''
  comment: Optional[str] = None
  author: Optional[str] = None