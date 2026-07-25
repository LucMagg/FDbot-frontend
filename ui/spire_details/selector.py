from __future__ import annotations
from typing import TYPE_CHECKING
import discord
import discord.ui

if TYPE_CHECKING:
  from sessions.spire_details import SpireDetailsSession


class MapSelector(discord.ui.Select):
  def __init__(self, session: SpireDetailsSession, row: int):
    self.session = session
    page = session.state.page
    choices_start = page * 24
    choices_end = min(choices_start + 24, len(session.state.choices))
    selected_name = session.state.details_data.selected_map.get('name') if session.state.details_data.selected_map else None
    options = [discord.SelectOption(
      label=session.state.choices[i].get('label'),
      value=session.state.choices[i].get('value'),
      default=(session.state.choices[i].get('value') == selected_name),
    ) for i in range(choices_start, choices_end)]
    super().__init__(placeholder=session.state.placeholder, options=options, row=row)

  async def callback(self, interaction: discord.Interaction):
    self.session.logger.log_only('debug', f'[SPIRE DETAILS] Map selected: {self.values[0]}')
    await self.session.ui.set_interaction(interaction)
    self.session.state.selection = self.values[0]
    await self.session.flow_manager()


class BracketSelector(discord.ui.Select):
  def __init__(self, session: SpireDetailsSession, row: int):
    self.session = session
    options = [discord.SelectOption(
      label=c.get('label'),
      value=c.get('value'),
      emoji=c.get('emoji'),
    ) for c in session.state.choices]
    super().__init__(placeholder=session.state.placeholder, options=options, row=row)

  async def callback(self, interaction: discord.Interaction):
    self.session.logger.log_only('debug', f'[SPIRE DETAILS] Bracket selected: {self.values[0]}')
    await self.session.ui.set_interaction(interaction)
    self.session.state.selection = self.values[0]
    await self.session.flow_manager()