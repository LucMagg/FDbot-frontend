from __future__ import annotations
from typing import TYPE_CHECKING
import discord.ui

from ui.level.buttons import RootChoiceButton, RootValidationButton, RewardChoiceButton, RewardValidationButton

if TYPE_CHECKING:
  from sessions.level import LevelSession

class RootView(discord.ui.View):
  def __init__(self, session: LevelSession):
    super().__init__(timeout=session.ui.timeout)
    self.session = session
    self.build()

  def build(self):
    self.clear_items()
    for reward_node in self.session.state.reward_types:
      self.add_item(RootChoiceButton(session=self.session, reward_node=reward_node))
    label = self.session.state.get_validation_label()
    if label:
      self.add_item(RootValidationButton(session=self.session, label=label, disabled=not self.session.state.can_validate()))

  async def on_timeout(self):
    await self.session.handle_timeout('Root view')


class RewardView(discord.ui.View):
  def __init__(self, session: LevelSession):
    super().__init__(timeout=session.ui.timeout)
    self.session = session
    self.build()

  def build(self):
    self.clear_items()
    for choice_node in self.session.state.get_current_group_choices():
      self.add_item(RewardChoiceButton(session=self.session, choice_node=choice_node))
    label = self.session.state.get_validation_label()
    if label:
      self.add_item(RewardValidationButton(session=self.session, label=label, disabled=not self.session.state.can_validate()))

  async def on_timeout(self):
    await self.session.handle_timeout('Reward view')