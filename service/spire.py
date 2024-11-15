from datetime import datetime

class SpireService:
  def __init__(self, bot):
    self.bot = bot  

  async def display_scores_after_posting_spire(self, tier):
    print('display scores begin')
    scores = await self.bot.back_requests.call("getSpireDataScores", False, [{'type': 'player'}])
    to_return = f'## Classement actuel en {tier} ##\n'
    to_return += self.scores_str(scores=scores, tier=tier, key='current_climb')
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
      to_return += f'{item.get('username')} [{item.get('guild')}]\n'

    return to_return