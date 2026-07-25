from dataclasses import dataclass, field


@dataclass(slots=True)
class PetState():
  pet: str = None
  pet_dict: dict = field(default_factory=dict)
  heroes_by_pet: list = field(default_factory=list)
  active_talent: dict = field(default_factory=dict)