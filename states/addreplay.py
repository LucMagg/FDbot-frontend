from dataclasses import dataclass, field
  

@dataclass(slots=True)
class AddReplayState():
  link: str = ''
  processed_link: dict[str, dict[str, str]] = field(default_factory=dict)