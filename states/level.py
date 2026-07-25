from dataclasses import dataclass, field
from typing import Optional
  

@dataclass(slots=True)
class LevelState():
  # base
  name: dict[str, str] = field(default_factory=dict)
  standard_energy_cost: Optional[int] = None
  coop_energy_cost: Optional[int] = None
  # nav
  mode: str = 'root' # root | reward
  active_reward_index: int = 0
  current_group_id: Optional[str] = None
  # data
  reward_types: list[dict] = field(default_factory=list)
  selected_rewards: list[str] = field(default_factory=list)
  selections: dict[str, dict[str, set[str]]] = field(default_factory=dict)
  global_selected_rewards: list[dict] = field(default_factory=list)
  # labels
  next_label: Optional[str] = None
  submit_label: Optional[str] = None
  

  # Selection
  def is_selected(self, id: str) -> bool:
    if self.mode == 'root':
      return id in self.selected_rewards
    rid = self._current_reward_id()
    gid = self.current_group_id
    return rid in self.selections and gid in self.selections[rid] and id in self.selections[rid][gid]

  def toggle_selection(self, id: str):
    if self.mode == 'root':
      self._toggle_reward(id)
    else:
      self._toggle_choice(id)

  def _toggle_reward(self, rid: str):
    if rid in self.selected_rewards:
      self.selected_rewards.remove(rid)
    else:
      self.selected_rewards.append(rid)

  def _toggle_choice(self, cid: str):
    rid = self._current_reward_id()
    gid = self.current_group_id
    if not rid or not gid:
      return
    self.selections.setdefault(rid, {})
    self.selections[rid].setdefault(gid, set())
    if cid in self.selections[rid][gid]:
      self.selections[rid][gid].remove(cid)
    else:
      self.selections[rid][gid].add(cid)

  # Navigation
  def start_reward_flow(self) -> bool:
    if not self.selected_rewards:
      return False
    self.mode = 'reward'
    self.active_reward_index = 0
    return self._move_to_first_group_of_current_reward()

  def advance_reward_flow(self) -> str:
    groups = self._current_groups()
    if self.current_group_id and groups:
      idx = self._current_group_index(groups)
      if idx is not None and idx + 1 < len(groups):
        self.current_group_id = groups[idx + 1]['gid']
        return 'reward' # Next group exists -> same reward
    self.active_reward_index += 1 # Else move to next reward
    if self.active_reward_index >= len(self.selected_rewards):
      self.current_group_id = None
      return 'finish' # No next reward -> end flow
    self._move_to_first_group_of_current_reward()
    return 'reward'

  # Getter
  def get_current_group_choices(self) -> list[dict]:
    groups = self._current_groups()
    if not groups or not self.current_group_id:
      return []
    group = next((g for g in groups if g['gid'] == self.current_group_id), None)
    return group.get('choices', []) if group else []
  
  def get_reward_node(self) -> Optional[dict]:
    rid = self._current_reward_id()
    return self._reward_by_id(rid) if rid else None

  def get_current_group_node(self) -> Optional[dict]:
    groups = self._current_groups()
    if not groups or not self.current_group_id:
      return None
    return next((g for g in groups if g['gid'] == self.current_group_id), None)

  # Validation
  def validate_root(self) -> str:
    if not self.selected_rewards:
      return 'invalid'
    self.mode = 'reward'
    self.active_reward_index = 0
    while self.active_reward_index < len(self.selected_rewards):
      groups = self._current_groups()
      if groups:
        self.current_group_id = groups[0]['gid']
        return 'reward'
      self.active_reward_index += 1
    self.current_group_id = None
    return 'finish'

  def can_validate(self) -> bool:
    if self.mode == 'root':
      return bool(self.selected_rewards)
    group = self.get_current_group_node()
    if not group:
      return True
    rid = self._current_reward_id()
    gid = self.current_group_id
    return bool(self.selections.get(rid, {}).get(gid))

  def get_validation_label(self) -> Optional[str]:
    if not self.can_validate():
      return None
    if self.mode == 'root':
      return self.next_label if self._has_any_groups() else self.submit_label
    return self.next_label if not self._reward_completed() else self.submit_label

  # Final data
  def build_global_selected_rewards(self) -> list[dict]:
    result = []
    for rid in self.selected_rewards:
      reward = self._reward_by_id(rid)
      groups = {g['gid']: g for g in reward.get('choices', [])}
      reward_entry = self._build_dict(
        reward,
        [self._build_dict(
          group,
          [self._build_dict(choice) for choice in group.get('choices', []) if choice['cid'] in selected_cids]
        )
        for gid, selected_cids in self.selections.get(rid, {}).items() if (group := groups.get(gid))
        ]
      )
      result.append(reward_entry)
    return result

  # Helpers
  def _current_reward_id(self) -> Optional[str]:
    if self.active_reward_index >= len(self.selected_rewards):
      return None
    return self.selected_rewards[self.active_reward_index]

  def _reward_by_id(self, rid: str) -> dict:
    return next(r for r in self.reward_types if r['rid'] == rid)

  def _current_reward_node(self) -> Optional[dict]:
    rid = self._current_reward_id()
    return self._reward_by_id(rid) if rid else None

  def _current_groups(self) -> list[dict]:
    node = self._current_reward_node()
    return node.get('choices', []) if node else []

  def _move_to_first_group_of_current_reward(self) -> bool:
    groups = self._current_groups()
    if groups:
      self.current_group_id = groups[0]['gid']
      return True
    return False

  def _current_group_index(self, groups: list[dict]) -> Optional[int]:
    for i, g in enumerate(groups):
      if g['gid'] == self.current_group_id:
        return i
    return None

  def _reward_completed(self) -> bool:
    groups = self._current_groups()
    if not groups:
      return True
    rid = self._current_reward_id()
    for g in groups:
      if rid not in self.selections:
        return False
      if g['gid'] not in self.selections[rid]:
        return False
      if not self.selections[rid][g['gid']]:
        return False
    return True

  def _has_any_groups(self) -> bool:
    return any(self._reward_by_id(rid).get('choices') for rid in self.selected_rewards)

  def _has_next_step(self) -> bool:
    groups = self._current_groups()
    if self.current_group_id and groups:
      idx = self._current_group_index(groups)
      if idx is not None and idx + 1 < len(groups):
        return True
    return self.active_reward_index + 1 < len(self.selected_rewards)

  def _build_dict(self, raw: dict, choices: Optional[list[dict]] = None) -> dict:
    return {
      'id': raw.get('rid') or raw.get('gid') or raw.get('cid'),
      'name': raw.get('name'),
      'icon': raw.get('icon'),
      'grade': raw.get('grade'),
      'has_quantity': raw.get('has_quantity'),
      'choices': choices or None
    }