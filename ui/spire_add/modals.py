from __future__ import annotations
import discord.ui
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from sessions.spire_add import SpireAddSession

class Modal(discord.ui.Modal):
  def __init__(self, session: SpireAddSession):
    super().__init__(title=session.ui.title, timeout=session.ui.timeout)
    self.session = session
    self.inputs = []
    self.build()

  def build(self):
    self.clear_items()
    for idx, input in enumerate(self.session.state.modal_inputs):
      self.inputs.append(discord.ui.TextInput(label=input.get('label'), placeholder=input.get('placeholder'), custom_id=f'input{idx}', required=True))
      self.add_item(self.inputs[idx])
  
  async def on_submit(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.inputs = {self.session.state.modal_inputs[idx].get('key'): input.value for idx, input in enumerate(self.inputs)}
    await self.session.flow_manager()
  
  async def on_timeout(self):
    await self.session.handle_timeout(whichone=f'Modal | step : {self.session.state.step}')