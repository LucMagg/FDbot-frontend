from typing import Optional

import discord
import requests

from config import DB_PATH
from utils.misc_utils import pluriel
from collections import defaultdict


class LevelService:

  @staticmethod
  def get_reward_response(response_type, emojis, level_name, reward_type, reward_quantity, gear_qualities, dust_qualities, reward_quality: Optional[str] = ''):
    match response_type:
      case 'add':
        level = LevelService.add_reward(level_name, reward_type, reward_quantity, reward_quality)
        title = f'Récompense ajoutée au niveau {level.get('name')}'
        description = 'Merci d\'avoir ajouté une récompense à ce niveau !\n'
      case 'show':
        level = LevelService.get_level(level_name)
        title = f'Statistiques pour le niveau {level.get('name')}'
        description = ''
    
    quantities_str = LevelService.get_rewards_str(level.get('rewards', []), emojis, gear_qualities, dust_qualities)
    description += f"Statistiques actuelles pour ce niveau sur {quantities_str}"    
    
    return {'title': title, 'description': description, 'color': 'blue'}

  @staticmethod
  def add_reward(level_name, reward_type, reward_quantity, reward_quality: str):
    data = {
      "type": reward_type,
      "quantity": reward_quantity,
      "quality": reward_quality
    }

    return requests.post(f"{DB_PATH}levels/{level_name}/reward", json=data).json()

  @staticmethod
  def get_rewards_str(rewards, emojis, gear_qualities, dust_qualities):  
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
          icon = LevelService.get_potion_emoji(emojis)
          multilines = False
        case 'gear':
          icon = next((g.get('icon') for g in gear_qualities if g.get('name') == r.get('quality')), None)
          multilines = False # à remplacer par True quand on gèrera les types d'item dans les rewards :D
        case 'dust':
          icon = next((d.get('icon') for d in dust_qualities if d.get('name') == r.get('quality')), None)
          multilines = False
          if len(r.get('rewards')) > 1:
            multilines = True

      if multilines:
        to_append = f"{icon} {r.get('quality', '')} {r.get('type')} : {format(r.get('total_appearances') / total_appearances, '.2%')} ({r.get('total_appearances')}), soit :\n"
        for l in r['rewards']:
          to_append += f"* {l.get('quantity')} {r.get('type')}s {format(l.get('appearances') / r.get('total_appearances'), '.2%')} ({l.get('appearances')})\n"
      else:
        quantity = ' '
        if r.get('rewards')[0].get('quantity') > 1:
          quantity = f" {r.get('rewards')[0].get('quantity')} "
        to_append = f"{icon}{quantity}{r.get('quality', '')} {r.get('type')} : {format(r.get('total_appearances') / total_appearances, '.2%')} ({r.get('total_appearances')})\n"
      lines.append(to_append)
   
    return f'{total_appearances} récompense{pluriel(total_appearances)} recueillie{pluriel(total_appearances)} :\n' + '\n'.join([l for l in lines])

  @staticmethod
  def get_potion_emoji(emojis):
    potion_emoji = discord.utils.get(emojis, name='potion')
    return str(potion_emoji) if potion_emoji else ''
  
  @staticmethod
  def get_level(level_name):
    return requests.get(f"{DB_PATH}levels/{level_name}").json()