import discord
from datetime import datetime, timezone, timedelta

from ui.base_ui import BaseUiData
from services.loop.spire.state import RankingState
from services.loop.spire.view import RankingView

from utils.misc_utils import rank_text


class SpireRankingSession:
  def __init__(self, data: dict):
    self.bot = data.get('bot')
    self.logger = self.bot.logger

    self.state = RankingState()
    self.return_msg = self.bot.message.get_message('spire ranking loop')

    self.all_languages = ['en', 'fr']

  # Session entry point
  async def start(self):
    try:
      self.state.spire_date = datetime.now(tz=timezone.utc)
      diff = self.state.spire_date - self.state.spire_start_time
      days = diff.days % self.state.spire_length
      self.logger.log('info', f'[LOOP] Spire ranking loop triggered {self.state.spire_date} | days: {days}')
      if days % 3 == 0 and days > 0:
        await self._send_spire_rankings()
      elif days == 0:
        await self._send_spire_start()
    except Exception as e:
      self.logger.log('error', f'[LOOP] Spire ranking loop error : {e}')

  # Send spire start message
  async def _send_spire_start(self):
    self.state.spire_date = (self.state.spire_date - timedelta(days=2, minutes=1)).isoformat()
    if not await self._set_channels(whichone='start'):
      return
    if not await self._create_new_spire():
      return
    for channel_data in self.state.channels:
      channel = self.bot.get_channel(channel_data.get('discord_channel_id'))
      if not channel:
        continue
      ui = BaseUiData.from_channel(channel, self.bot)
      ui.response = {'description': self.return_msg.get(ui.langcode).get('start message'),'color': self.return_msg.get('color')}
      await ui.send()
      self.logger.log('info', f'[LOOP] Spire ranking loop start sent in channel {channel}')

  # Send spire ranking message
  async def _send_spire_rankings(self):
    self.state.spire_date = (self.state.spire_date - timedelta(minutes=1)).isoformat()
    if not await self._set_channels(whichone='score'):
      return
    if not await self._get_scores():
      return
    for channel_data in self.state.channels:
      try:
        channel = self.bot.get_channel(channel_data.get('discord_channel_id'))
        if not channel:
          self.logger.log('warning', f'[LOOP] Spire ranking score channel {channel_data.get('discord_channel_id')} not found')
          continue
        old_message_id = channel_data.get('ranking_message_id')
        self.logger.log('warning', f'[LOOP] Spire ranking old message id {old_message_id}')
        ui = BaseUiData.from_channel(channel, self.bot)
        if old_message_id:
          ui.previous_message = await channel.fetch_message(old_message_id)
          ui.unpin = True
        ui.current_page = 0
        ui.pin = True
        ui.labels = {'previous': self.return_msg.get(ui.langcode).get('previous'), 'next': self.return_msg.get(ui.langcode).get('next')}
        ui.rankings = await self._build_rankings_for_channel(ui)
        if not ui.rankings:
          self.logger.log('warning', f'[LOOP] Spire ranking score | no ui rankings')
          continue
        await self.render_message(ui)
        await self._add_message_id(ui.message)
        self.logger.log('info', f'[LOOP] Spire ranking score sent in channel {channel}')
      except Exception as e:
        self.logger.log('error', f'[LOOP] Spire ranking score | error while sending rankings : {e}')

  # Ranking message handlers
  #    render message
  async def render_message(self, ui: BaseUiData):
    self._enable_buttons(ui)
    ui.view = RankingView(session=self, ui=ui)
    ui.response = ui.rankings[ui.current_page]
    await ui.send()

  #    next page
  async def next_page(self, ui: BaseUiData):
    ui.current_page += 1
    await self.render_message(ui)

  #    previous page
  async def previous_page(self, ui: BaseUiData):
    ui.current_page -= 1
    await self.render_message(ui)

  #    enable/disable buttons
  def _enable_buttons(self, ui: BaseUiData):
    ui.is_previous_button_disabled = True if ui.current_page == 0 else False
    ui.is_next_button_disabled = True if ui.current_page == len(ui.rankings) - 1 else False

  # Rankings builder
  async def _build_rankings_for_channel(self, ui: BaseUiData) -> list[dict]:
    allowed_user_ids = {member.id for member in ui.channel.members if not member.bot}
    filtered_player_scores = {
      'climb': self.state.player_scores.get('climb'),
      'spire': self.state.player_scores.get('spire'),
      'current_climb': {},
      'current_spire': {},
    }
    allowed_guilds = set()
    for ranking_type in ('current_climb', 'current_spire'):
      for tier, scores in self.state.player_scores.get(ranking_type, {}).items():
        filtered_scores = [score for score in scores if score.get('user_id') in allowed_user_ids]
        if not filtered_scores:
          continue
        filtered_player_scores[ranking_type][tier] = filtered_scores
        allowed_guilds.update(score.get('guild') for score in filtered_scores if score.get('guild'))
    filtered_guild_scores = {
      'climb': self.state.guild_scores.get('climb'),
      'spire': self.state.guild_scores.get('spire'),
      'current_climb': {},
      'current_spire': {},
    }
    for ranking_type in ('current_climb', 'current_spire'):
      for tier, scores in self.state.guild_scores.get(ranking_type, {}).items():
        filtered_scores = [score for score in scores if score.get('guild') in allowed_guilds]
        if not filtered_scores:
          continue
        filtered_guild_scores[ranking_type][tier] = filtered_scores
    pages = []
    all_tiers = set()
    all_tiers.update(filtered_player_scores.get('current_spire', {}).keys())
    all_tiers.update(filtered_guild_scores.get('current_spire', {}).keys())
    for tier in self.state.all_tiers:
      if tier not in all_tiers:
        continue
      embed = self._build_embed(ui.langcode, tier, filtered_player_scores, filtered_guild_scores)
      pages.append(embed)
    return pages
  
  # Rankings helpers
  #   _build_embed
  def _build_embed(self, lang: str, tier: str, player_scores: dict, guild_scores: dict) -> dict:
    description = f'# __{self._translate(tier, lang).capitalize()}__ \n'
    if guild_scores.get('climb') < 4:
      description += (
        f'## {self.return_msg.get(lang).get('climb rank 1')} {player_scores.get('climb')}'
        f'{self._translate(rank_text(player_scores.get('climb')), lang)} {self.return_msg.get(lang).get('climb rank 2')}\n'
        f'{self._build_section(lang, tier, player_scores.get('current_climb'), guild_scores.get('current_climb'))}\n'
      )
    if guild_scores.get('climb') > 1:
      description += (
        f'## {self.return_msg.get(lang).get('spire rank') if guild_scores.get('climb') < 4 else self.return_msg.get(lang).get('final rank')}\n'
        f'{self._build_section(lang, tier, player_scores.get('current_spire'), guild_scores.get('current_spire'))}\n'
      )
    return {'description': description, 'color': self.return_msg.get('color')}

  #    build sections
  def _build_section(self, lang: str, tier: str, player_scores: dict, guild_scores: dict) -> str:
    result = ''
    player_tier_scores = player_scores.get(tier)
    if player_tier_scores:
      max_length = min(20, len(player_tier_scores))
      result += (
        f'### __{self.return_msg.get(lang).get('players')}__\n'
        f'{self._display_scores(player_tier_scores[:max_length])}\n\n'
      )
    else:
      result += f'{self.return_msg.get(lang).get('no score 1')}{self._translate(tier, lang)}{self.return_msg.get(lang).get('no score 2')}\n'
    guild_tier_scores = guild_scores.get(tier)
    if guild_tier_scores:
      max_length = min(20, len(guild_tier_scores))
      result += (
        f'### __{self.return_msg.get(lang).get('guilds')}__\n'
          f'{self._display_scores(guild_tier_scores[:max_length])}\n'
      )      
    return result

  #    display scores
  def _display_scores(self, scores: dict) -> str:
    return '\n'.join(
      f'{self.state.icons[i] if i < len(self.state.icons) else f'{i + 1}.'} '
      f'{item.get('score')} - '
      f'{(
        f'{item.get('username')} [{item.get('guild')}]'
        if item.get('username')
        else item.get('guild')
      )}'
      for i, item in enumerate(scores)
    )

  # Request helpers
  #    set channels
  async def _set_channels(self, whichone: str) -> bool:
    result = await self.bot.back_requests.call('getSpireByDate', [{'date': self.state.spire_date}])
    if 'error' in result:
      self.logger.log('error', f'[LOOP] Spire ranking {whichone} : error while getting spire')
      return False
    self.state.channels = result.get('channels')
    return True
  
  #    create new spire
  async def _create_new_spire(self) -> bool:
    self.state.spire_date = datetime.now(tz=timezone.utc).isoformat()
    result = await self.bot.back_requests.call('getSpireByDate', [{'date': self.state.spire_date}])
    if 'error' in result:
      self.logger.log('error', '[LOOP] Spire ranking start : error while creating new spire')
      return False
    return True
  
  #    add message id (to the right spire in spires collection)
  async def _add_message_id(self, message: discord.Message) -> bool:
    result = await self.bot.back_requests.call('addMessageId', [{'date': self.state.spire_date, 'channel_id': message.channel.id, 'ranking_message_id': message.id}])
    if 'error' in result:
      self.logger.log('error', f'[LOOP] Spire ranking score : error while adding ranking_message_id')
      return False
    return True
  
  #    delete message id (in the right spire in spires collection)
  async def _delete_message_id(self, message: discord.Message) -> bool:
    result = await self.bot.back_requests.call('deleteMessageId', [{'date': self.state.spire_date, 'channel_id': message.channel.id, 'ranking_message_id': message.id}])
    if 'error' in result:
      self.logger.log('error', f'[LOOP] Spire ranking score : error while deleting ranking_message_id')
      return False
    return True
  
  #    get scores
  async def _get_scores(self) -> bool:
    self.state.player_scores = await self.bot.back_requests.call('getSpireDataScores', [{'type': 'player', 'date': self.state.spire_date}])
    self.state.guild_scores = await self.bot.back_requests.call('getSpireDataScores', [{'type': 'guild', 'date': self.state.spire_date}])
    if 'error' in self.state.player_scores or 'error' in self.state.guild_scores:
      self.logger.log('error', f'[LOOP] Spire ranking score : error while getting scores')
      return False
    return True
  
  # Translate helper
  def _translate(self, key: str, lang: str) -> str:
    return self.bot.language.translate_from_key(text_to_translate=key, lang=lang)