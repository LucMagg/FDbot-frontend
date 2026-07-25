from __future__ import annotations
import discord.ui
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from sessions.reward_add import RewardAddSession


class PreviousButton(discord.ui.Button):
  def __init__(self, session: RewardAddSession):
    self.session = session
    is_disabled = True if self.session.state.page == 0 else False
    super().__init__(label=self.session.state.previous_label, style=discord.ButtonStyle.grey if is_disabled else discord.ButtonStyle.blurple, disabled=is_disabled)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.page -= 1
    await self.session._render_selector_view()


class NextButton(discord.ui.Button):
  def __init__(self, session: RewardAddSession):
    self.session = session
    is_disabled = True if (self.session.state.page + 1) * 24 > len(self.session.state.choices) else False
    super().__init__(label=self.session.state.next_label, style=discord.ButtonStyle.grey if is_disabled else discord.ButtonStyle.blurple, disabled=is_disabled)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.page += 1
    await self.session._render_selector_view()


class ValidationButton(discord.ui.Button):
  def __init__(self, session: RewardAddSession):
    self.session = session
    super().__init__(label=self.session.state.ok_label, style=discord.ButtonStyle.green)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    await self.session.advance()


class CancelButton(discord.ui.Button):
  def __init__(self, session: RewardAddSession):
    self.session = session
    super().__init__(label=self.session.state.cancel_label, style=discord.ButtonStyle.red)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    await self.session._render_cancel()