from __future__ import annotations
import discord.ui
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from services.loop.loop_ui import LoopUi
  from services.loop.spire.spire_ranking import SpireRankingSession


class RankingView(discord.ui.View):
  def __init__(self, session: SpireRankingSession, ui: LoopUi):
    super().__init__(timeout=60 * 60 * 24 * 3)
    self.add_item(PreviousButton(session, ui))
    self.add_item(NextButton(session, ui))


class PreviousButton(discord.ui.Button):
  def __init__(self, session: SpireRankingSession, ui: LoopUi):
    self.session = session
    self.ui = ui
    super().__init__(label=self.ui.labels.get('previous'), style=discord.ButtonStyle.blurple, disabled=self.ui.is_previous_button_disabled)

  async def callback(self, interaction: discord.Interaction):
    await self.ui.set_interaction(interaction)
    await self.session.previous_page(self.ui)


class NextButton(discord.ui.Button):
  def __init__(self, session: SpireRankingSession, ui: LoopUi):
    self.session = session
    self.ui = ui
    super().__init__(label=self.ui.labels.get('next'), style=discord.ButtonStyle.blurple, disabled=self.ui.is_next_button_disabled)

  async def callback(self, interaction: discord.Interaction):
    await self.ui.set_interaction(interaction)
    await self.session.next_page(self.ui)