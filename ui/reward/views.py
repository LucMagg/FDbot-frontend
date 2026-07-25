from __future__ import annotations
from typing import TYPE_CHECKING
import discord.ui

from ui.reward.selector import RewardSelector, TimesSelector
from ui.reward.buttons import ValidationButton, CancelButton, PreviousButton, NextButton

if TYPE_CHECKING:
  from sessions.reward_add import RewardAddSession

class SelectorView(discord.ui.View):
  def __init__(self, session: RewardAddSession):
    super().__init__(timeout=session.ui.timeout)
    self.session = session
    self.build()

  def build(self):
    self.clear_items()
    self.add_item(RewardSelector(session=self.session))
    if len(self.session.state.choices) > 25:
      self.add_item(PreviousButton(session=self.session))
      self.add_item(NextButton(session=self.session))

  async def on_timeout(self):
    await self.session.handle_timeout(f'Selector view | step : {self.session.state.step}')

class ValidationView(discord.ui.View):
  def __init__(self, session: RewardAddSession):
    super().__init__(timeout=session.ui.timeout)
    self.session = session
    self.build()

  def build(self):
    self.clear_items()
    self.add_item(TimesSelector(session=self.session))
    self.add_item(CancelButton(session=self.session))
    self.add_item(ValidationButton(session=self.session))

  async def on_timeout(self):
    await self.session.handle_timeout(f'Validation view')