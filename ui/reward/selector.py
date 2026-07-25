from __future__ import annotations
from typing import TYPE_CHECKING
import discord.ui
import re
import emoji

if TYPE_CHECKING:
  from sessions.reward_add import RewardAddSession


class RewardSelector(discord.ui.Select):
  def __init__(self, session: RewardAddSession):
    self.session = session
    choices_start = 0 + (24 * self.session.state.page)
    choices_end = min(24 + (24 * self.session.state.page), len(self.session.state.choices))
    selector_options = [discord.SelectOption(
      label=self.session.state.choices[i].get('label'), 
      value=self.session.state.choices[i].get('value'), 
      emoji=self._get_emoji_from_icon(self.session.state.choices[i].get('icon')))
      for i in range(choices_start, choices_end)]
    super().__init__(placeholder=self.session.state.placeholder, options=selector_options)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.selection = self.values[0]
    await self.session.advance()

  def _get_emoji_from_icon(self, icon: str):
    if not icon or 'customIcon' in icon:
      return None
    unicode_match = re.match(r'\\U([0-9a-fA-F]{8})', icon)
    if unicode_match:
      return chr(int(unicode_match.group(1), 16))
    return emoji.emojize(icon)
  
class TimesSelector(discord.ui.Select):
  def __init__(self, session: RewardAddSession):
    self.session = session
    selector_options = [discord.SelectOption(
      label=o.get('label'), 
      value=o.get('value'))
      for o in self.session.state.choices]
    super().__init__(placeholder=str(self.session.state.selected.get('times')), options=selector_options)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.selected['times'] = int(self.values[0])
    await self.session._render_validation_view()