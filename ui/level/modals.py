from __future__ import annotations
import discord.ui
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
  from sessions.level import LevelSession

class NameLocalizationsModal(discord.ui.Modal):
  def __init__(self, session: LevelSession, fields: list[Dict[str, str]]):
    super().__init__(title=session.ui.title, timeout=session.ui.timeout)
    self.session = session
    self.input_name: list[discord.ui.TextInput] = []
    for index, field in enumerate(fields):
      self.input_name.append(discord.ui.TextInput(label=field.get('label'), custom_id=f'input{index}', required=True))
      self.add_item(self.input_name[index])

  async def on_submit(self, interaction: discord.Interaction):
    data = [i.value for i in self.input_name]
    await self.session.handle_modal_submit(interaction=interaction, data=data)

  async def on_timeout(self):
    await self.session.handle_timeout(whichone='NameLocalizations modal')