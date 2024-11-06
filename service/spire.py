import discord
import datetime as discord_time
from datetime import datetime
from discord.ext import tasks

from utils.misc_utils import get_discord_color

#local_tz = datetime.now().astimezone().tzinfo
#time = discord_time.time(hour=12, minute=0, tzinfo=local_tz)

class SpireService:
  def __init__(self, bot):
    self.bot = bot
    self.send_spire_results.start()
    
  async def display_scores_after_posting_spire(self, tier):
    print('display scores begin')
    scores = await self.bot.back_requests.call("getSpireDataScores", False, [{'type': 'player'}])
    to_return = f'## Classement actuel en {tier} ##\n'
    print(to_return)
    to_return += self.scores_to_str(scores=scores, tier=tier, key='current_climb')
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
      print(tier)
      if tier in player_scores.get(key).keys() or tier in guild_scores.get(key).keys():
        to_return +='\n'
        to_return += '-' * 40
        to_return += f'\n### {tier} ###\n'
        if tier in player_scores.get(key).keys():
          print(to_return)
          to_return += f'\n__ Joueurs __\n'
          to_return += self.scores_to_str(scores=player_scores, tier=tier, key=key)
        if tier in guild_scores.get(key).keys():
          to_return += f'\n__ Guildes __\n'
          to_return += self.scores_to_str(scores=guild_scores, tier=tier, key=key)
    return to_return

  def scores_to_str(self, scores, tier: str, key: str):
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
  
"""
  @tasks.loop(time=time)
  async def send_spire_results(self):
    channel = self.bot.get_channel(1119633026989707367)
    description = await self.display_scores_from_scheduler(date='2024-11-03T18:00:00')
    response = discord.Embed(title='', description=description, color= get_discord_color('blue'))
    await channel.send(embed=response)

  @send_spire_results.before_loop
  async def before_loop(self):
    await self.bot.wait_until_ready()
"""