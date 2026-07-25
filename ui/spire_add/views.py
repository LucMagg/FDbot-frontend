from __future__ import annotations
from typing import TYPE_CHECKING
import discord.ui

from ui.spire_add.selector import Selector
from ui.spire_add.buttons import PreviousButton, NextButton, YesButton, NoButton, MainButton, ValidationButton, OkButton

if TYPE_CHECKING:
  from sessions.spire_add import SpireAddSession


class MainView(discord.ui.View):
  def __init__(self, session: SpireAddSession):
    super().__init__(timeout=session.ui.timeout)
    self.session = session
    self.build()

  def build(self):
    self.clear_items()
    for whichone in ['guild', 'tier', 'climb', 'score']:
      self.add_item(MainButton(session=self.session, whichone=whichone))
    self.add_item(ValidationButton(session=self.session))

  async def on_timeout(self):
    await self.session.handle_timeout(f'Main view')


class SelectorView(discord.ui.View):
  def __init__(self, session: SpireAddSession):
    super().__init__(timeout=session.ui.timeout)
    self.session = session
    self.build()

  def build(self):
    self.clear_items()
    self.add_item(Selector(session=self.session))
    if len(self.session.state.choices) > 25:
      self.add_item(PreviousButton(session=self.session))
      self.add_item(NextButton(session=self.session))

  async def on_timeout(self):
    await self.session.handle_timeout(f'Selector view | step : {self.session.state.step}')


class YesNoView(discord.ui.View):
  def __init__(self, session: SpireAddSession):
    super().__init__(timeout=session.ui.timeout)
    self.session = session
    self.build()

  def build(self):
    self.clear_items()
    self.add_item(NoButton(session=self.session))
    self.add_item(YesButton(session=self.session))

  async def on_timeout(self):
    await self.session.handle_timeout(f'Yes/no view')


class ErrorView(discord.ui.View):
  def __init__(self, session: SpireAddSession):
    super().__init__(timeout=session.ui.timeout)
    self.session = session
    self.build()

  def build(self):
    self.clear_items()
    self.add_item(OkButton(session=self.session))

  async def on_timeout(self):
    await self.session.handle_timeout(f'Error view')