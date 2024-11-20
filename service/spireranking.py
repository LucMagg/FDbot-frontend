import discord
from datetime import datetime, timedelta
from discord.ext import tasks

from utils.misc_utils import get_discord_color
from utils.sendMessage import SendMessage


class SpireRankingService:
  def __init__(self, bot):
    self.bot = bot
    self.current_page = 0
    self.message = None
    self.view = None
    self.response = None
    self.rankings = []
    self.send_message = SendMessage(self.bot)
    self.spire_start_time = datetime.fromisoformat("2024-11-06T11:00:00+00:00")
    self.spire_length = 14
    self.send_spire_results.start()
    self.date_to_get = None

  class RankingsView(discord.ui.View):
    def __init__(self, outer):
      print('init rankings view begin')
      super().__init__(timeout=60*60*24*3)
      self.outer = outer
      self.add_item(self.outer.RankingsButton(outer=outer, label='Précédent', custom_id='previous'))
      print('previous add')
      self.add_item(self.outer.RankingsButton(outer=outer, label='Suivant', custom_id='next'))
      print('next add')
      print('init rankings view end')
    
  class RankingsButton(discord.ui.Button):
    def __init__(self, outer, label, custom_id):
      print(f'{custom_id} button init begin')
      self.outer = outer
      print('here')
      self.id = custom_id
      print('there')

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
              await self.bot.back_requests.call("deleteMessageId", False, [{'date': self.date_to_get, 'channel_id': channel_data.get('discord_channel_id')}])
    except Exception as e:
      print(e)
  
  async def build_response(self):
    self.rankings = await self.get_rankings()
    self.view = self.RankingsView(outer=self)
    self.response = discord.Embed(title='', description=self.rankings[self.current_page], color=get_discord_color('blue'))
 
  async def post_messages(self, channels):
    try:
      for channel_data in channels:
        channel = self.bot.get_channel(channel_data.get('discord_channel_id'))
        message = await channel.send(embed=self.response, view=self.view)
        pinned = await self.bot.back_requests.call("addMessageId", False, [{'date': self.date_to_get, 'channel_id': channel_data.get('discord_channel_id'), 'message_id': message.id}])
        if pinned:
          await message.pin()
    except Exception as e:
      print(e)

  async def send_spire_rankings(self):
    channels = await self.get_channels()
    print(channels)
    await self.unpin_old_messages(channels)
    await self.build_response()
    await self.post_messages(channels)

  async def send_spire_start(self):
    channels = await self.get_channels()
    print(channels)
    await self.unpin_old_messages(channels)
    description = '# Début de la bataille des guildes ! # \nQue les bonus et l\'absence de moves foireux soient avec vous :grin:\nBon courage à tous :wink:'
    self.response = discord.Embed(title='', description=description, color=get_discord_color('blue'))
    for channel_data in channels:
      channel = self.bot.get_channel(channel_data.get('discord_channel_id'))
      await channel.send(embed=self.response)
      
  @tasks.loop(time=datetime.time(hour=11, minute=0, tzinfo=datetime.timezone.utc))
  #@tasks.loop(seconds=30)
  async def send_spire_results(self):
    now = datetime.now(datetime.timezone.utc)
    diff = now - self.spire_start_time
    days = diff.days % self.spire_length
    #days = 3
    print(f'{now} || loop: {days}')
    if days % 3 == 0 and days > 0:
      self.date_to_get = (now - timedelta(minutes=1)).isoformat()
      await self.send_spire_rankings()
    if days == 0:
      self.date_to_get = (now - timedelta(days=2, minutes=1)).isoformat()
      await self.send_spire_start()

  @send_spire_results.before_loop
  async def before_loop(self):
    await self.bot.wait_until_ready()