from __future__ import annotations
import discord.ui
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from sessions.reward_add import RewardAddSession

class QuantityModal(discord.ui.Modal):
  def __init__(self, session: RewardAddSession):
    super().__init__(title=session.ui.title, timeout=session.ui.timeout)
    self.session = session
    self.build()

  def build(self):
    self.clear_items()
    self.input = discord.ui.TextInput(label=self.session.state.modal_label, placeholder=self.session.state.placeholder, custom_id='input', required=True)
    self.add_item(self.input)
  
  async def on_submit(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    return await self.session.handle_modal_submit(self.input.value)
  
  async def on_timeout(self):
    await self.session.handle_timeout(whichone='QuantityModal')