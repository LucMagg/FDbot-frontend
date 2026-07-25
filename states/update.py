from dataclasses import dataclass


@dataclass(slots=True)
class UpdateState():
  type: str = None