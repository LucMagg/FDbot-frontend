from __future__ import annotations
from typing import TYPE_CHECKING
import discord.ui
import discord

if TYPE_CHECKING:
  from sessions.spire_details import SpireDetailsSession


class BonusModal(discord.ui.Modal):
  def __init__(self, session: SpireDetailsSession):
    super().__init__(title=session.ui.title, timeout=session.ui.timeout)
    self.session = session
    self.inputs: list[discord.ui.TextInput] = []
    self.build()

  def build(self):
    self.clear_items()
    for idx, input in enumerate(self.session.state.modal_inputs):
      self.inputs.append(discord.ui.TextInput(label=input.get('label'), default=input.get('default', None), placeholder=input.get('placeholder'), custom_id=f'input{idx}', required=False))
      self.add_item(self.inputs[idx])

  async def on_submit(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.inputs = {self.session.state.modal_inputs[idx].get('key'): input.value for idx, input in enumerate(self.inputs)}
    await self.session.flow_manager()

  async def on_timeout(self):
    await self.session.handle_timeout(f'[SPIRE DETAILS] Bonus modal timeout | step : {self.session.state.step}')


class TalentsModal(discord.ui.Modal):
  def __init__(self, session: SpireDetailsSession):
    super().__init__(title=session.ui.title, timeout=session.ui.timeout)
    self.session = session
    self.inputs: list[discord.ui.TextInput] = []
    self.build()

  def build(self):
    self.clear_items()
    for idx, input in enumerate(self.session.state.modal_inputs):
      self.inputs.append(discord.ui.TextInput(label=input.get('label'), default=input.get('default', None), placeholder=input.get('placeholder'), custom_id=input.get('key'), required=True))
      self.add_item(self.inputs[idx])

  async def on_submit(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.inputs = {input.custom_id: input.value for input in self.inputs}
    await self.session.flow_manager()

  async def on_timeout(self):
    await self.session.handle_timeout(f'[SPIRE DETAILS] Talents modal timeout | step : {self.session.state.talents_step}/3')