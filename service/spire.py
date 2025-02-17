from datetime import datetime, timezone

class SpireService:
  def __init__(self, bot):
    self.bot = bot  

  async def display_scores_after_posting_spire(self, tier, climb):
    print('display scores begin')
    spire = await self.bot.back_requests.call("getSpireByDate", False, [{'date': datetime.now(tz=timezone.utc).isoformat()}])
    date_to_display = next((d.get('start_date') for d in spire.get('climbs') if d.get('number') == climb), None)

    if date_to_display is not None:
      scores = await self.bot.back_requests.call("getSpireDataScores", False, [{'type': 'player', 'date': date_to_display}])
      current_climb = self.get_current_climb(spire)

      if current_climb == climb:
        title_to_add = 'actuel'
      else:
        title_to_add = f'du climb #{climb}'
        
      to_return = f'## Classement {title_to_add} en {tier} ##\n'
      to_return += self.scores_str(scores=scores, tier=tier, key='current_climb')
      return to_return
    return 'Erreur'
  
  def get_current_climb(self, spire):
    now = datetime.now(tz=timezone.utc)
    for climb in spire.get('climbs'):
      start = datetime.strptime(climb['start_date'], "%a, %d %b %Y %H:%M:%S %Z")
      end = datetime.strptime(climb['end_date'], "%a, %d %b %Y %H:%M:%S %Z")
      start = start.replace(tzinfo=timezone.utc)
      end = end.replace(tzinfo=timezone.utc)
      if start <= now <= end:
        return climb.get('number')
    return None

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