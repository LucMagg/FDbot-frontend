from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar


@dataclass(slots=True)
class RankingState:
  spire_date: datetime = field(default_factory=datetime.now)
  channels: list[dict] = field(default_factory=list)
  rankings: list[dict] = field(default_factory=list)
  player_scores: list[dict] = field(default_factory=list)
  guild_scores: list[dict] = field(default_factory=list)

  spire_start_time: ClassVar[datetime] = datetime.fromisoformat('2024-11-06T11:00:00+00:00')
  spire_length: ClassVar[int] = 14
  all_tiers: ClassVar[list[str]] = ['Platinum', 'Gold', 'Silver', 'Bronze', 'Hero', 'Adventurer']
  icons: ClassVar[list[str]] = [':first_place:', ':second_place:', ':third_place:']