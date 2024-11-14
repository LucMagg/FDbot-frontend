from datetime import datetime

class SpireService:
  def __init__(self, bot):
    self.bot = bot  

  async def display_scores_after_posting_spire(self, tier):
    print('display scores begin')
    scores = await self.bot.back_requests.call("getSpireDataScores", False, [{'type': 'player'}])
    to_return = f'## Classement actuel en {tier} ##\n'
    to_return += self.scores_str(scores=scores, tier=tier, key='current_climb')

  def get_all_brackets_scores(self, player_scores: dict, guild_scores: dict, key: str, tier: str) -> str:
    to_return = ''
    
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