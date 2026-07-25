from __future__ import annotations
import discord.ui
import re
import emoji
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from sessions.level import LevelSession


class RootChoiceButton(discord.ui.Button):
  def __init__(self, session: LevelSession, reward_node: dict):
    self.session = session
    self.reward_node = reward_node
    self.rid = reward_node['rid']
    label = reward_node['name'].get(session.ui.langcode).capitalize()
    selected = session.state.is_selected(self.rid)
    style = discord.ButtonStyle.primary if selected else discord.ButtonStyle.secondary
    super().__init__(label=label,style=style)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.toggle_selection(self.rid)
    await self.session.render_root()


class RootValidationButton(discord.ui.Button):
  def __init__(self, session: LevelSession, label: str, disabled: bool):
    self.session = session
    disabled = not session.state.can_validate()
    super().__init__(label=label, style=discord.ButtonStyle.success, disabled=disabled)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    await self.session.validate_root_selection()


class RewardChoiceButton(discord.ui.Button):
  def __init__(self, session: LevelSession, choice_node: dict):
    self.session = session
    self.choice_node = choice_node
    self.cid = choice_node['cid']
    label = choice_node['name'].get(session.ui.langcode).capitalize()
    selected = session.state.is_selected(self.cid)
    style = discord.ButtonStyle.primary if selected else discord.ButtonStyle.secondary
    emoji = self.get_emoji_from_icon(self.choice_node.get('icon'))
    super().__init__(label=label,style=style,emoji=emoji)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.toggle_selection(self.cid)
    await self.session.render_reward()

  def get_emoji_from_icon(self, icon: str):
    if not icon or 'customIcon' in icon:
      return None
    unicode_match = re.match(r'\\U([0-9a-fA-F]{8})', icon)
    if unicode_match:
      return chr(int(unicode_match.group(1), 16))
    return emoji.emojize(icon)


class RewardValidationButton(discord.ui.Button):
  def __init__(self, session: LevelSession, label: str, disabled: bool):
    self.session = session
    disabled = not session.state.can_validate()
    super().__init__(label=label, style=discord.ButtonStyle.success, disabled=disabled)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    await self.session.validate_reward_selection()