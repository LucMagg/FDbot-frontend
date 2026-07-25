import discord
from datetime import datetime, timezone
from services.loop.spire.state import RankingState

from ui.base_ui import BaseUiData
from utils.misc_utils import get_discord_color, rank_text


class SpireReminderSession:
  def __init__(self, data: dict):
    self.bot = data.get('bot')
    self.logger = self.bot.logger

    self.state = RankingState()
    self.return_msg = self.bot.message.get_message('spire reminder loop')

  async def start(self):
    try:
      self.state.spire_date = datetime.now(tz=timezone.utc)
      diff = self.state.spire_date - self.state.spire_start_time
      days = diff.days % self.state.spire_length + 1
      self.logger.log_only('info', f'[LOOP] Spire reminder triggered {self.state.spire_date} | days: {days}')
      if days % 3 == 0 and days > 3:
        await self._send_spire_reminder()
    except Exception as e:
      self.logger.log_only('error', f'[LOOP] Spire reminder error : {e}')

  # Send spire reminder message
  async def _send_spire_reminder(self):
    self.state.spire_date = self.state.spire_date.isoformat()
    if not await self._set_channels():
      return
    all_users_to_remind = await self._get_users_to_remind()
    for channel_data in self.state.channels:
      try:
        channel = self.bot.get_channel(channel_data.get('discord_channel_id'))
        if not channel:
          continue
        ui = BaseUiData.from_channel(channel, self.bot)
        allowed_user_ids = {member.id for member in ui.channel.members if not member.bot}
        users_in_channel = [user for user in all_users_to_remind if user in allowed_user_ids]
        if len(users_in_channel) > 0:
          await self._render_message(ui, users_in_channel)
      except Exception as e:
        self.logger.log_only('error', f'[LOOP] Spire reminder | error while sending reminder : {e}')

  # Render message helper
  async def _render_message(self, ui: BaseUiData, users_in_channel: list):
    description = (
      f'## {self.state.player_scores.get('climb')}{self._translate(rank_text(self.state.player_scores.get('climb')), ui.langcode)}'
      f' {self.return_msg.get(ui.langcode).get('climb')} \n'
      f'{'\n'.join([f'<@{u}>' for u in users_in_channel])}'
      f'\n{self.return_msg.get(ui.langcode).get('message')}'
    )
    ui.response = discord.Embed(description=description, color=get_discord_color(self.return_msg.get('color')))
    await ui.send()

  # Get users to remind helper
  async def _get_users_to_remind(self) -> list[int]:
    result = await self._get_scores()
    if not result:
      return
    current_climb = self.state.player_scores.get('current_climb') or {}
    current_spire = self.state.player_scores.get('current_spire') or {}
    current_climb_users = {player.get('user_id') for tier in current_climb.values() for player in tier}
    return [player.get('user_id') for tier in current_spire.values() for player in tier if player.get('user_id') not in current_climb_users]

  # Request helpers
  #    set channels
  async def _set_channels(self) -> bool:
    result = await self.bot.back_requests.call('getSpireByDate', [{'date': self.state.spire_date}])
    if 'error' in result:
      self.logger.log_only('error', f'[LOOP] Spire reminder : error while getting spire')
      return False
    self.state.channels = result.get('channels')
    return True
  
  #    get scores
  async def _get_scores(self) -> bool:
    self.state.player_scores = await self.bot.back_requests.call('getSpireDataScores', [{'type': 'player', 'date': self.state.spire_date}])
    if 'error' in self.state.player_scores:
      self.logger.log_only('error', f'[LOOP] Spire reminder : error while getting scores')
      return False
    return True
  
  # Translate helper
  def _translate(self, key: str, lang: str) -> str:
    return self.bot.language.translate_from_key(text_to_translate=key, lang=lang)