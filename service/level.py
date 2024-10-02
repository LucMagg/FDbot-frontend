from typing import Optional

import discord
import requests

from config import DB_PATH
from utils.misc_utils import pluriel
from collections import defaultdict


class LevelService:
  def __init__(self, bot):
    self.bot = bot
    self.gear_qualities = [g for g in bot.static_data.qualities if g['type'] == 'gear']
    self.dust_qualities = bot.static_data.dusts

  async def get_reward_response(self, response_type, emojis, level_name, reward_type, reward_quantity, reward_quality: Optional[str] = ''):
    match response_type:
      case 'add':
        level = await self.add_reward(level_name, reward_type, reward_quantity, reward_quality)
        description = f'# {level.get('name')} #\n'
        description += 'Merci d\'avoir ajouté une récompense à ce niveau ! :kissing_heart:\n\n'

      case 'show':
        level = await self.bot.back_requests.call('getLevelByName', False, [level_name])
        description = f'# {level.get('name')} #\n'
    
    quantities_str = self.get_rewards_str(level.get('rewards', []), emojis)
    description += f"### Statistiques actuelles sur {quantities_str}"    
    
    return {'title': '', 'description': description, 'color': 'blue'}

  async def add_reward(self, level_name, reward_type, reward_quantity, reward_quality: str):
    data = {
      "type": reward_type,
      "quantity": reward_quantity,
      "quality": reward_quality
    }
    return await self.bot.back_requests.call('addReward', False, [level_name, data])

  def get_rewards_str(self, rewards, emojis):  
    has_quality = False
    for r in rewards:
      if 'quality' in r.keys():
        has_quality = True

    if has_quality:
      grouped_rewards = defaultdict(lambda: {'rewards': [], 'total_appearances': 0})
      for r in rewards:
        key = (r['type'], r.get('quality', ''))
        grouped_rewards[key]['rewards'].append({
          'quantity': r['quantity'],
          'appearances': r['appearances']
        })
        grouped_rewards[key]['total_appearances'] += r['appearances']

      result = [{
        'type': key[0],
        'quality': key[1],
        'rewards': value['rewards'],
        'total_appearances': value['total_appearances']
      } for key, value in grouped_rewards.items()]

    else:
      result = [{
        'type': r.get('type'),
        'rewards': [{'quantity': r.get('quantity')}],
        'total_appearances': r.get('appearances')
      } for r in rewards]
      

    result.sort(key=lambda x: -x['total_appearances'])
    total_appearances = sum([r.get('total_appearances') for r in result])

    lines = []
    for r in result:
      icon = ''
      match r.get('type'):
        case 'gold':
          icon = ':moneybag:'
          multilines = False
        case 'potions':
          icon = self.get_potion_emoji(emojis)
          multilines = False
        case 'gear':
          icon = next((g.get('icon') for g in self.gear_qualities if g.get('name') == r.get('quality')), None)
          multilines = False # à remplacer par True quand on gèrera les types d'item dans les rewards :D
        case 'dust':
          icon = next((d.get('icon') for d in self.dust_qualities if d.get('name') == r.get('quality')), None)
          multilines = False
          if len(r.get('rewards')) > 1:
            multilines = True

      if multilines:
        to_append = f"{icon} {r.get('quality', '')} {r.get('type')} : {format(r.get('total_appearances') / total_appearances, '.2%')} ({r.get('total_appearances')}), soit :\n"
        for l in r['rewards']:
          to_append += f"\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0• {l.get('quantity')} {r.get('type')}s {format(l.get('appearances') / r.get('total_appearances'), '.2%')} ({l.get('appearances')})\n"
      else:
        quantity = ' '
        if r.get('rewards')[0].get('quantity') > 1:
          quantity = f" {r.get('rewards')[0].get('quantity')} "
        to_append = f"{icon}{quantity}{r.get('quality', '')} {r.get('type')} : {format(r.get('total_appearances') / total_appearances, '.2%')} ({r.get('total_appearances')})\n"
      lines.append(to_append)
   
    return f'{total_appearances} récompense{pluriel(total_appearances)} recueillie{pluriel(total_appearances)} : ###\n {'\n'.join([l for l in lines])}'

  def get_potion_emoji(self, emojis):
    potion_emoji = discord.utils.get(emojis, name='potion')
    return str(potion_emoji) if potion_emoji else ''