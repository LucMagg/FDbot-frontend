import discord
import datetime as discord_time
from datetime import datetime
from discord.ext import tasks

from utils.misc_utils import get_discord_color

#local_tz = datetime.now().astimezone().tzinfo
#time = discord_time.time(hour=12, minute=0, tzinfo=local_tz)

class SpireService:
  def __init__(self, bot, channel_ids):
    self.bot = bot
    self.channel_ids = channel_ids
    self.spire_start_time = datetime.fromisoformat("2024-11-06T12:00:00")
    self.spire_length = 14
    #self.send_spire_results.start()

  async def display_scores_after_posting_spire(self, tier):
    print('display scores begin')
    scores = await self.bot.back_requests.call("getSpireDataScores", False, [{'type': 'player'}])
    to_return = f'## Classement actuel en {tier} ##\n'
    print(to_return)
    to_return += self.scores_str(scores=scores, tier=tier, key='current_climb')
    print(to_return)
    return to_return
  
  async def display_scores_from_scheduler(self, date):
    player_scores = await self.bot.back_requests.call("getSpireDataScores", False, [{'type': 'player'}])
    guild_scores = await self.bot.back_requests.call("getSpireDataScores", False, [{'type': 'guild'}])
    if player_scores.get('climb') < 4:
      print('here')
      to_return = f'# Classements du climb #{player_scores.get('climb')} #\n'
      print(to_return)
      to_return += self.get_all_brackets_scores(player_scores=player_scores, guild_scores=guild_scores, key='current_climb')
      print(to_return)
      if 'current_spire' in player_scores.keys():
        to_return += f'\n# Classements de la spire #\n'
        print(to_return)
        to_return += self.get_all_brackets_scores(player_scores=player_scores, guild_scores=guild_scores, key='current_spire')
    else:
      print('there')
      to_return = f'# Classements finaux #\n'
      print(to_return)
      
      to_return += self.get_all_brackets_scores(player_scores=player_scores, guild_scores=guild_scores, key='current_spire')
    
    return to_return

  def get_all_brackets_scores(self, player_scores, guild_scores, key):
    to_return = ''
    for tier in ['Platinum', 'Gold', 'Silver', 'Bronze', 'Hero', 'Adventurer']:
      if tier in player_scores.get(key).keys() or tier in guild_scores.get(key).keys():
        to_return += f'\n{'-' * 40}\n### {tier} ###\n'
        if tier in player_scores.get(key).keys():
          player_scores_str = self.scores_str(scores=player_scores, tier=tier, key=key)
          to_return += f'\n__ Joueurs __\n{player_scores_str}'
        if tier in guild_scores.get(key).keys():
          guild_scores_str = self.scores_str(scores=guild_scores, tier=tier, key=key)
          to_return += f'\n__ Guildes __\n{guild_scores_str}'

    return to_return

  def scores_str(self, scores, tier: str, key: str):
    to_return = ''
    icons = [':first_place:', ':second_place:', ':third_place:']
    scores_data = scores.get(key).get(tier)
    print(scores_data)

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

  async def send_spire_start_message(self):
    description = await self.display_scores_from_scheduler(date='2024-11-03T18:00:00')
    await self.send_message('spire start', description)

  async def send_spire_end_message(self):
    description = await self.display_scores_from_scheduler(date='2024-11-03T18:00:00')
    await self.send_message('spire end', description)

  async def send_climb_end_message(self):
    description = await self.display_scores_from_scheduler(date='2024-11-03T18:00:00')
    await self.send_message('climb end', description)

  async def send_message(self, title, description):
    response = discord.Embed(title=title, description=description, color=get_discord_color('blue'))
    for channel_id in self.channel_ids:
      channel = self.bot.get_channel(channel_id)
      await channel.send(embed=response)

"""
  @tasks.loop(time=time)
  async def send_spire_results(self):
    diff = datetime.now() - self.spire_start_time
    days = diff.days % self.spire_length
    if days == 0:
      await self.send_spire_start_message()
    elif days == 12:
      await self.send_spire_end_message()
    elif days % 3 == 0:
      await self.send_climb_end_message()

  @send_spire_results.before_loop
  async def before_loop(self):
    await self.bot.wait_until_ready()
"""