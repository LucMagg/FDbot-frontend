from __future__ import annotations
from typing import TYPE_CHECKING
import discord
import discord.ui
 
from ui.spire_details.buttons import DetailButton, FinishButton, CancelButton, WaterButton, LavaButton, YesButton, NoButton, TalentsContinueButton, TalentsChangeButton, FinalValidateButton, FinalChangeButton, MapPreviousButton, MapNextButton
from ui.spire_details.selector import MapSelector, BracketSelector
 
if TYPE_CHECKING:
  from sessions.spire_details import SpireDetailsSession
 
 
class MainView(discord.ui.View):
  def __init__(self, session: SpireDetailsSession):
    super().__init__(timeout=session.ui.timeout)
    self.session = session
    self.build()
 
  def build(self):
    self.clear_items()
    for key in self.session.state.main_buttons:
      self.add_item(DetailButton(session=self.session, key=key, row=0))
    self.add_item(CancelButton(session=self.session, row=1))
    self.add_item(FinishButton(session=self.session, row=1))
 
  async def on_timeout(self):
    await self.session.handle_timeout('Initial view')
 
 
class MapView(discord.ui.View):
  def __init__(self, session: SpireDetailsSession):
    super().__init__(timeout=session.ui.timeout)
    self.session = session
    self.build()
 
  def build(self):
    self.clear_items()
    self.add_item(MapSelector(session=self.session, row=0))
    if len(self.session.state.choices) > 25:
      self.add_item(MapPreviousButton(session=self.session, row=1))
      self.add_item(MapNextButton(session=self.session, row=1))
    self.add_item(CancelButton(session=self.session, row=1))
 
  async def on_timeout(self):
    await self.session.handle_timeout('Map view')
 
 
class WaterOrLavaView(discord.ui.View):
  def __init__(self, session: SpireDetailsSession):
    super().__init__(timeout=session.ui.timeout)
    self.session = session
    self.build()
 
  def build(self):
    self.clear_items()
    self.add_item(WaterButton(session=self.session, row=1))
    self.add_item(LavaButton(session=self.session, row=1))
 
  async def on_timeout(self):
    await self.session.handle_timeout('Water or lava view')
 
 
class BonusValidationView(discord.ui.View):
  def __init__(self, session: SpireDetailsSession):
    super().__init__(timeout=session.ui.timeout)
    self.session = session
    self.build()
 
  def build(self):
    self.clear_items()
    self.add_item(NoButton(session=self.session))
    self.add_item(YesButton(session=self.session))
 
  async def on_timeout(self):
    await self.session.handle_timeout(f'{' '.join(self.session.state.step.split('_')).capitalize()} view')
 
 
class BracketView(discord.ui.View):
  def __init__(self, session: SpireDetailsSession):
    super().__init__(timeout=session.ui.timeout)
    self.session = session
    self.build()
 
  def build(self):
    self.clear_items()
    self.add_item(BracketSelector(session=self.session, row=0))
 
  async def on_timeout(self):
    await self.session.handle_timeout('Bracket view')
 
 
class TalentsBetweenView(discord.ui.View):
  def __init__(self, session: SpireDetailsSession):
    super().__init__(timeout=session.ui.timeout)
    self.session = session
    self.build()
 
  def build(self):
    self.clear_items()
    self.add_item(TalentsChangeButton(session=self.session))
    self.add_item(TalentsContinueButton(session=self.session))
 
  async def on_timeout(self):
    await self.session.handle_timeout(f'Talents between view (step {self.session.state.talents_step}/3)')
 
 
class FinalView(discord.ui.View):
  def __init__(self, session: SpireDetailsSession):
    super().__init__(timeout=session.ui.timeout)
    self.session = session
    self.build()
 
  def build(self):
    self.clear_items()
    self.add_item(FinalChangeButton(session=self.session))
    self.add_item(FinalValidateButton(session=self.session))
 
  async def on_timeout(self):
    await self.session.handle_timeout('Final view')