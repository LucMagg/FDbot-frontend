from __future__ import annotations
import discord.ui
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from sessions.spire_add import SpireAddSession


class MainButton(discord.ui.Button):
  def __init__(self, session: SpireAddSession, whichone: str):
    self.session = session
    label = getattr(self.session.state, f'{whichone}_label')
    style = discord.ButtonStyle.blurple if not getattr(self.session.state.spire_data, f'is_{whichone}_valid')() else discord.ButtonStyle.grey
    super().__init__(label=label, style=style, custom_id=whichone, row=0)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.step = self.custom_id
    await self.session.flow_manager()


class ValidationButton(discord.ui.Button):
  def __init__(self, session: SpireAddSession):
    self.session = session
    is_disabled = not(self.session.state.spire_data.is_done())
    super().__init__(label=self.session.state.validation_label, style=discord.ButtonStyle.green, disabled=is_disabled, row=1)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.validate = True
    await self.session.flow_manager()

class PreviousButton(discord.ui.Button):
  def __init__(self, session: SpireAddSession):
    self.session = session
    is_disabled = True if self.session.state.page == 0 else False
    super().__init__(label=self.session.state.previous_label, style=discord.ButtonStyle.grey if is_disabled else discord.ButtonStyle.blurple, disabled=is_disabled)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.page -= 1
    await self.session._render_selector_view()


class NextButton(discord.ui.Button):
  def __init__(self, session: SpireAddSession):
    self.session = session
    is_disabled = True if (self.session.state.page + 1) * 24 > len(self.session.state.choices) else False
    super().__init__(label=self.session.state.next_label, style=discord.ButtonStyle.grey if is_disabled else discord.ButtonStyle.blurple, disabled=is_disabled)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.page += 1
    await self.session._render_selector_view()


class YesButton(discord.ui.Button):
  def __init__(self, session: SpireAddSession):
    self.session = session
    super().__init__(label=self.session.state.yes_label, style=discord.ButtonStyle.green)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.validate = True
    await self.session.flow_manager()


class NoButton(discord.ui.Button):
  def __init__(self, session: SpireAddSession):
    self.session = session
    super().__init__(label=self.session.state.no_label, style=discord.ButtonStyle.red)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.validate = False
    await self.session.flow_manager()


class OkButton(discord.ui.Button):
  def __init__(self, session: SpireAddSession):
    self.session = session
    super().__init__(label=self.session.state.ok_label, style=discord.ButtonStyle.green)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    await self.session.flow_manager()