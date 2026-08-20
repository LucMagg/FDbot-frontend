from __future__ import annotations
from typing import TYPE_CHECKING
import discord.ui
import discord

if TYPE_CHECKING:
  from sessions.spire_details import SpireDetailsSession


class DetailButton(discord.ui.Button):
  def __init__(self, session: SpireDetailsSession, key: str, row: int):
    self.session = session
    self.key = key
    label = getattr(self.session.state, f'{key}_label')
    done = self._is_done()
    style = discord.ButtonStyle.blurple if not done else discord.ButtonStyle.grey
    is_disabled = True if key == 'hero_bonus' and session.state.details_data.climb == 2 else False
    super().__init__(label=label, style=style, disabled=is_disabled, custom_id=key, row=row)

  def _is_done(self) -> bool:
    match self.key:
      case 'map':
        return self.session.state.details_data.is_map_valid()
      case 'hero_bonus':
        return self.session.state.details_data.is_hero_bonus_valid()
      case 'monster_bonus':
        return self.session.state.details_data.is_monster_bonus_valid()
      case 'talents':
        return self.session.state.details_data.is_talents_valid()

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.selection = self.key
    await self.session.flow_manager()


class FinishButton(discord.ui.Button):
  def __init__(self, session: SpireDetailsSession, row: int):
    self.session = session
    is_disabled = not(self.session.state.details_data.has_any_detail())
    super().__init__(label=session.state.finish_label, style=discord.ButtonStyle.success, disabled=is_disabled, row=row)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.validate = True
    await self.session.flow_manager()


class CancelButton(discord.ui.Button):
  def __init__(self, session: SpireDetailsSession, row: int):
    self.session = session
    super().__init__(label=session.state.cancel_label, style=discord.ButtonStyle.danger, row=row)

  async def callback(self, interaction: discord.Interaction):
    self.session.logger.log('debug', '[SPIRE DETAILS] Canceled')
    await self.session.ui.set_interaction(interaction)
    self.session.state.clear_nav()
    self.session.state.step = 'cancel' if self.session.state.step == 'main' else 'main'
    await self.session.flow_manager()


class MapPreviousButton(discord.ui.Button):
  def __init__(self, session: SpireDetailsSession, row: int):
    self.session = session
    is_disabled = session.state.page == 0
    super().__init__(label=session.state.previous_label, style=discord.ButtonStyle.grey if is_disabled else discord.ButtonStyle.blurple, disabled=is_disabled, row=row)

  async def callback(self, interaction: discord.Interaction):
    self.session.logger.log('debug', '[SPIRE DETAILS] Map previous button')
    await self.session.ui.set_interaction(interaction)
    self.session.state.page -= 1
    await self.session._render_map_view()


class MapNextButton(discord.ui.Button):
  def __init__(self, session: SpireDetailsSession, row: int):
    self.session = session
    is_disabled = (self.session.state.page + 1) * 24 >= len(self.session.state.choices)
    super().__init__(label=session.state.next_label, style=discord.ButtonStyle.grey if is_disabled else discord.ButtonStyle.blurple, disabled=is_disabled, row=row)

  async def callback(self, interaction: discord.Interaction):
    self.session.logger.log('debug', '[SPIRE DETAILS] Map next button')
    await self.session.ui.set_interaction(interaction)
    self.session.state.page += 1
    await self.session._render_map_view()


class MapValidateButton(discord.ui.Button):
  def __init__(self, session: SpireDetailsSession, row: int):
    self.session = session
    selected = session.state.details_data.selected_map
    label = session.state.next_label if (selected and selected.get('has_water_or_lava')) else session.state.validate_label
    super().__init__(label=label, style=discord.ButtonStyle.success, row=row)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.validate = True
    await self.session.flow_manager()


class WaterButton(discord.ui.Button):
  def __init__(self, session: SpireDetailsSession, row: int):
    self.session = session
    super().__init__(label=session.state.water_label, style=discord.ButtonStyle.primary, row=row)

  async def callback(self, interaction: discord.Interaction):
    self.session.logger.log('debug', '[SPIRE DETAILS] Map with water')
    await self.session.ui.set_interaction(interaction)
    self.session.state.selection = 'water'
    await self.session.flow_manager()


class LavaButton(discord.ui.Button):
  def __init__(self, session: SpireDetailsSession, row: int):
    self.session = session
    super().__init__(label=session.state.lava_label, style=discord.ButtonStyle.danger, row=row)

  async def callback(self, interaction: discord.Interaction):
    self.session.logger.log('debug', '[SPIRE DETAILS] Map with lava')
    await self.session.ui.set_interaction(interaction)
    self.session.state.selection = 'lava'
    await self.session.flow_manager()


class YesButton(discord.ui.Button):
  def __init__(self, session: SpireDetailsSession):
    self.session = session
    super().__init__(label=session.state.yes_label, style=discord.ButtonStyle.success)

  async def callback(self, interaction: discord.Interaction):
    self.session.logger.log('debug', f'[SPIRE DETAILS] {' '.join(self.session.state.step.split('_')).capitalize()} submit')
    await self.session.ui.set_interaction(interaction)
    self.session.state.validate = True
    await self.session.flow_manager()


class NoButton(discord.ui.Button):
  def __init__(self, session: SpireDetailsSession):
    self.session = session
    super().__init__(label=session.state.no_label, style=discord.ButtonStyle.danger)

  async def callback(self, interaction: discord.Interaction):
    self.session.logger.log('debug', f'[SPIRE DETAILS] {' '.join(self.session.state.step.split('_')).capitalize()} cancel')
    await self.session.ui.set_interaction(interaction)
    self.session.state.validate = False
    await self.session.flow_manager()


class TalentsChangeButton(discord.ui.Button):
  def __init__(self, session: SpireDetailsSession):
    self.session = session
    super().__init__(label=session.state.change_label, style=discord.ButtonStyle.danger)

  async def callback(self, interaction: discord.Interaction):
    self.session.logger.log('debug', f'[SPIRE DETAILS] {self.session.state.talents_step}/3 change')
    await self.session.ui.set_interaction(interaction)
    self.session.state.validate = False
    await self.session.flow_manager()


class TalentsContinueButton(discord.ui.Button):
  def __init__(self, session: SpireDetailsSession):
    self.session = session
    label = session.state.continue_label if session.state.talents_step < 3 else session.state.validate_label
    super().__init__(label=label, style=discord.ButtonStyle.success)

  async def callback(self, interaction: discord.Interaction):
    self.session.logger.log('debug', f'[SPIRE DETAILS] {self.session.state.talents_step}/3 change')
    await self.session.ui.set_interaction(interaction)
    self.session.state.validate = True
    await self.session.flow_manager()


class FinalChangeButton(discord.ui.Button):
  def __init__(self, session: SpireDetailsSession):
    self.session = session
    super().__init__(label=session.state.change_label, style=discord.ButtonStyle.danger)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    self.session.state.validate = False
    self.session.state.step = 'initial'
    await self.session.flow_manager()


class FinalValidateButton(discord.ui.Button):
  def __init__(self, session: SpireDetailsSession):
    self.session = session
    super().__init__(label=session.state.validate_label, style=discord.ButtonStyle.success)

  async def callback(self, interaction: discord.Interaction):
    await self.session.ui.set_interaction(interaction)
    await self.session.confirm_and_post()