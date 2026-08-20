from __future__ import annotations
from typing import TYPE_CHECKING
import discord.ui

if TYPE_CHECKING:
  from sessions.spire_add import SpireAddSession


class Selector(discord.ui.Select):
  def __init__(self, session: SpireAddSession):
    self.session = session
    choices_start = 0 + (24 * self.session.state.page)
    choices_end = min(24 + (24 * self.session.state.page), len(self.session.state.choices))
    selector_options = [discord.SelectOption(
      label=self.session.state.choices[i].get('label'), 
      value=self.session.state.choices[i].get('value'))
      for i in range(choices_start, choices_end)]
    super().__init__(placeholder=self.session.state.placeholder, options=selector_options)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.selection = self.values[0]
    self.session.logger.log('debug', f'[SPIRE ADD] selected: {self.session.state.selection} | type: {type(self.session.state.selection)}')
    await self.session.flow_manager()