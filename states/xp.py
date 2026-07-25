from dataclasses import dataclass, field


@dataclass(slots=True)
class XpState():
  stars: int = None
  current_ascend: str = None
  current_level: int = None
  target_ascend: str = None
  target_level: int = None
  xp_data: list[dict] = field(default_factory=list[dict])
  xp_table: list[dict] = field(default_factory=list[dict])
  thresholds: list[dict] = field(default_factory=list[dict])
  threshold_table: list[dict] = field(default_factory=list[dict])
  ascends = ['A0', 'A1', 'A2', 'A3', 'A4']

  def check_for_errors(self) -> str|None:
    self.threshold_table = next((d for d in self.thresholds if d.get('hero_stars') == self.stars), None)
    current_error = self._check_input_error(self.current_ascend, self.current_level)
    if current_error:
      return f'{current_error} current'
    target_error = self._check_input_error(self.target_ascend, self.target_level)
    if target_error:
      return f'{target_error} target'
    if self.current_ascend == self.target_ascend and self.current_level == self.target_level:
      return 'same level'
    if int(self.current_ascend[1]) > int(self.target_ascend[1]):
      return 'ascend downgrade'
    if self.current_ascend == self.target_ascend and self.current_level > self.target_level:
      return 'level downgrade'
    if int(self.current_ascend[1]) + 1 == int(self.target_ascend[1]) and (self.current_level + 1) // 2 > self.target_level:
      return 'incorrect path'
    return None

  def _check_input_error(self, ascend: str, level: int) -> str|None:
    threshold_data = self.threshold_table.get(ascend)
    if level < threshold_data.get('level').get('min') or level > threshold_data.get('level').get('max'):
      return 'input error'
    return None
   
  def calculate_steps(self) -> list[dict]:
    self.xp_table = next((x.get('data') for x in self.xp_data if x.get('hero_stars') == self.stars), None)
    if not self.xp_table:
      return None
    steps = []
    level = self.current_level
    ascend = self.current_ascend
    ascend_idx = self.ascends.index(ascend)
    while (level, ascend) != (self.target_level, self.target_ascend):
      threshold = self._threshold(ascend)
      if threshold is not None and level >= threshold: #skip
        cost = self._cost(ascend)
        level, ascend, ascend_idx = self._ascend(level, ascend_idx)
        steps.append(self._step(0, cost.get('gold'), cost.get('potions'), ascend, level, True))
      else:
        next_level = self.target_level if ascend == self.target_ascend else threshold
        potions = sum(row.get(ascend) or 0 for row in self.xp_table if level < row.get('level') <= next_level)
        steps.append(self._step(potions, 0, 0, ascend, next_level, False)) #potions step
        if (next_level, ascend) == (self.target_level, self.target_ascend):
          break
        prev_ascend = ascend
        level, ascend, ascend_idx = self._ascend(next_level, ascend_idx)
        if ascend != prev_ascend:
          cost = self._cost(self._previous_ascend(ascend))
          steps.append(self._step(0, cost.get('gold'), cost.get('potions'), ascend, level, False)) #ascend step
    return steps
  
  def _ascend(self, level: int, ascend_idx: int) -> tuple[int, str, int]:
    if ascend_idx + 1 >= len(self.ascends):
      return level, self.ascends[ascend_idx], ascend_idx
    level = (level + 1) // 2
    ascend_idx += 1
    ascend = self.ascends[ascend_idx]
    return level, ascend, ascend_idx

  def _step(self, potions: int, gold: int, heroic: int, ascend: str, level: int, skip: bool) -> dict:
    return {
      'potions': potions,
      'gold': gold,
      'heroic': heroic,
      'ascend': ascend,
      'level': level,
      'skip': skip
    }
  
  def _threshold(self, ascend: str) -> int:
    return self.threshold_table[ascend].get('threshold')

  def _cost(self, ascend: str) -> dict:
    return self.threshold_table[ascend].get('cost')
  
  def _previous_ascend(self, ascend: str) -> str:
    return f'A{int(ascend[1]) - 1}'