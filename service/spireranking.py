import discord
from datetime import datetime, timedelta, timezone
from discord.ext import tasks

from utils.misc_utils import get_discord_color


class SpireRankingService:
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.current_page = 0
    self.message = None
    self.view = None
    self.response = None
    self.rankings = []
    self.spire_start_time = datetime.fromisoformat("2024-11-06T11:00:00+00:00")
    self.spire_length = 14
    self.send_spire_results.start()
    self.send_spire_reminder.start()
    self.date_to_get = None

  class RankingsView(discord.ui.View):
    def __init__(self, outer):
      super().__init__(timeout=60*60*24*3)
      self.outer = outer
      self.add_item(self.outer.RankingsButton(outer=outer, label='Précédent', custom_id='previous'))
      self.add_item(self.outer.RankingsButton(outer=outer, label='Suivant', custom_id='next'))
    
  class RankingsButton(discord.ui.Button):
    def __init__(self, outer, label, custom_id):
      self.outer = outer
      self.id = custom_id

      if (self.outer.current_page > 0 and self.id == 'previous') or (self.outer.current_page < len(self.outer.rankings) - 1 and self.id == 'next'):
        style = discord.ButtonStyle.primary
        disabled = False
      else:
        style = discord.ButtonStyle.secondary
        disabled = True
      super().__init__(style=style, label=label, custom_id=custom_id, disabled=disabled)

    async def callback(self, interaction: discord.Interaction):
      update = False
      if self.outer.current_page > 0 and self.id == 'previous':
        self.outer.current_page -= 1
        update = True
      if self.outer.current_page < len(self.outer.rankings) - 1 and self.id == 'next':
        self.outer.current_page += 1
        update = True
      if update:
        self.outer.response = discord.Embed(title='', description=self.outer.rankings[self.outer.current_page], color=get_discord_color('blue'))
        self.outer.view= self.outer.RankingsView(outer=self.outer)
        await interaction.response.edit_message(embed=self.outer.response, view=self.outer.view)


  async def get_rankings(self):
    player_scores = await self.bot.back_requests.call("getSpireDataScores", False, [{'type': 'player', 'date': self.date_to_get}])
    guild_scores = await self.bot.back_requests.call("getSpireDataScores", False, [{'type': 'guild', 'date': self.date_to_get}])
    to_return = []

    for tier in ['Platinum', 'Gold', 'Silver', 'Bronze', 'Hero', 'Adventurer']:
      to_append = ''
      if tier in player_scores.get('current_climb').keys() or tier in guild_scores.get('current_climb').keys():
        to_append = f'__# {tier} #__\n'
        to_append += f'## Classements du climb #{player_scores.get('climb')} ##\n'
        to_append += self.get_all_brackets_scores(player_scores=player_scores, guild_scores=guild_scores, key='current_climb', tier=tier)
      if 'current_spire' in player_scores.keys():
        if tier in player_scores.get('current_spire').keys() or tier in guild_scores.get('current_spire').keys():
          if player_scores.get('climb') < 4:
            to_append += f'\n# Classements de la spire #\n'
          else:
            to_append = f'# Classements finaux #\n'
            to_append += f'## {tier} ##\n'
          to_append += self.get_all_brackets_scores(player_scores=player_scores, guild_scores=guild_scores, key='current_spire', tier=tier)
      if to_append != '':
        to_return.append(to_append)
    return to_return

  def get_all_brackets_scores(self, player_scores: dict, guild_scores: dict, key: str, tier: str) -> str:
    to_return = '\n'
    
    if tier in player_scores.get(key).keys() or tier in guild_scores.get(key).keys():
      if tier in player_scores.get(key).keys():
        player_scores_str = self.scores_str(scores=player_scores, tier=tier, key=key)
        to_return += f'\n__### Joueurs ###__\n{player_scores_str}'
      if tier in guild_scores.get(key).keys():
        guild_scores_str = self.scores_str(scores=guild_scores, tier=tier, key=key)
        to_return += f'\n__### Guildes ###__\n{guild_scores_str}'

    return to_return

  def scores_str(self, scores, tier: str, key: str):
    to_return = ''
    icons = [':first_place:', ':second_place:', ':third_place:']
    scores_data = scores.get(key).get(tier)

    for i in range(len(scores_data)):
      item = scores_data[i]
      header = icons[i] if i < len(icons) else f'{i + 1}.'
      to_return += f'{header} {item.get('score')} - '
      if 'username' in item.keys():
        to_return += f'{item.get('username')} [{item.get('guild')}]'
      else:
        to_return += f'{item.get('guild')}'
      to_return += f'\n'
    return to_return
  
  async def get_channels(self):
    spire = await self.bot.back_requests.call("getSpireByDate", False, [{'date': self.date_to_get}])
    return spire.get('channels')
  
  async def unpin_old_messages(self, channels):
    try:
      for channel_data in channels:
        if channel_data.get('ranking_message_id') is not None:
          channel = self.bot.get_channel(channel_data.get('discord_channel_id'))
          if channel:
            message = await channel.fetch_message(channel_data.get('ranking_message_id'))
            if message and message.pinned:
              await message.unpin()
              await self.bot.back_requests.call("deleteMessageId", False, [{'date': self.date_to_get, 'channel_id': channel_data.get('discord_channel_id'), 'ranking_message_id': message.id}])
    except Exception as e:
      self.logger.error_log(f'Erreur de unpin_old_message : {e}')
  
  async def build_response(self):
    self.rankings = await self.get_rankings()
    self.view = self.RankingsView(outer=self)
    self.response = discord.Embed(title='', description=self.rankings[self.current_page], color=get_discord_color('blue'))
 
  async def post_messages(self, channels):
    try:
      for channel_data in channels:
        channel = self.bot.get_channel(channel_data.get('discord_channel_id'))
        message = await channel.send(embed=self.response, view=self.view)
        pinned = await self.bot.back_requests.call("addMessageId", False, [{'date': self.date_to_get, 'channel_id': channel_data.get('discord_channel_id'), 'ranking_message_id': message.id}])
        if pinned:
          await message.pin()
    except Exception as e:
      self.logger.error_log(f'Erreur de post_messages : {e}')

  async def send_spire_rankings(self):
    channels = await self.get_channels()
    await self.unpin_old_messages(channels)
    await self.build_response()
    await self.post_messages(channels)

  async def send_spire_start(self):
    channels = await self.get_channels()
    await self.unpin_old_messages(channels)

    spire_start = datetime.now(tz=timezone.utc).isoformat()
    await self.bot.back_requests.call("getSpireByDate", False, [{'date': spire_start}])
    description = '# Début de la bataille des guildes ! # \nQue les bonus et l\'absence de moves foireux soient avec vous :grin:\nBon courage à tous :wink:'
    self.response = discord.Embed(title='', description=description, color=get_discord_color('blue'))
    for channel_data in channels:
      channel = self.bot.get_channel(channel_data.get('discord_channel_id'))
      await channel.send(embed=self.response)
  
  def get_player_id_or_name(self, player):
    return ('id', player.get('user_id')) if player.get('user_id') is not None else ('username', player.get('username'))

  def compare_spire_scores(self, actual_scores):
    current_climb_users = {self.get_player_id_or_name(player) for tier in actual_scores.get('current_climb').values() for player in tier}
    self.logger.long_only('info', f'current_climb_users: {current_climb_users}')
    missing_climb_users = [{"username": player.get('username'), "user_id": player.get('user_id')} for tier in actual_scores.get('current_spire').values() for player in tier if self.get_player_id_or_name(player) not in current_climb_users]
    self.logger.long_only('info', f'missing_climb_users: {missing_climb_users}')
    return missing_climb_users
  
  async def get_users_in_guild(self, channel, all_users):
    if not channel or not channel.guild:
      return []
    guild = channel.guild
    members_in_guild = []
    for user in all_users:
      user_id = user.get('user_id')
      if user_id is not None:
        try:
          member = await guild.fetch_member(user_id)
          if member:
            members_in_guild.append(user_id)
        except (discord.NotFound, discord.HTTPException):
          continue        
    return members_in_guild

  async def send_reminder_message(self):
    channels = await self.get_channels()
    actual_scores = await self.bot.back_requests.call("getSpireDataScores", False, [{'type': 'player', 'date': self.date_to_get}])
    all_users_to_remind = self.compare_spire_scores(actual_scores)
    for channel_data in channels:
      channel = self.bot.get_channel(channel_data.get('discord_channel_id'))
      users_by_channel = await self.get_users_in_guild(channel, all_users_to_remind)
      if len(users_by_channel) > 0:
        description = f'# Climb {actual_scores.get('climb')} # \n'
        for user in users_by_channel:
          description += f'<@{str(user)}> '
        description += 'il vous reste 1 heure pour poster votre score et soutenir votre guilde :kissing_heart:'
        self.response = discord.Embed(title='', description=description, color=get_discord_color('blue'))
        await channel.send(embed=self.response)

  @tasks.loop(time=datetime.now(tz=timezone.utc).replace(hour=10, minute=0, second=0, microsecond=0).time())
  async def send_spire_reminder(self):
    try:
      now = datetime.now(tz=timezone.utc)
      diff = now - self.spire_start_time
      days = diff.days % self.spire_length + 1
      self.logger.log_only('info', f'reminder loop {now} || loop: {days}')
      if days % 3 == 0 and days > 3:
        self.date_to_get = (now - timedelta(minutes=1)).isoformat()
        await self.send_reminder_message()
    except Exception as e:
      self.logger.error_log(f'Erreur de reminder loop : {e}')

  @tasks.loop(time=datetime.now(tz=timezone.utc).replace(hour=11, minute=0, second=0, microsecond=0).time())
  async def send_spire_results(self):
    try:
      now = datetime.now(tz=timezone.utc)
      diff = now - self.spire_start_time
      days = diff.days % self.spire_length
      self.logger.log_only('info', f'score loop {now} || loop: {days}')
      if days % 3 == 0 and days > 0:
        self.date_to_get = (now - timedelta(minutes=1)).isoformat()
        await self.send_spire_rankings()
      if days == 0:
        self.date_to_get = (now - timedelta(days=2, minutes=1)).isoformat()
        await self.send_spire_start()
    except Exception as e:
      self.logger.error_log(f'Erreur de score loop : {e}')

  @send_spire_results.before_loop
  async def before_loop(self):
    await self.bot.wait_until_ready()

  @send_spire_reminder.before_loop
  async def before_loop(self):
    await self.bot.wait_until_ready()