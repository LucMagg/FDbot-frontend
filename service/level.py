from typing import Optional

import discord
import requests

from config import DB_PATH
from utils.misc_utils import pluriel


class LevelService:

  @staticmethod
  def get_reward_response(emojis, level_name, reward_type, reward_quantity, gear_qualities, dust_qualities, reward_quality: Optional[str] = ''):
    level = LevelService.add_reward(level_name, reward_type, reward_quantity, reward_quality)
    quantities_str = LevelService.get_rewards_str(level.get('rewards', []), emojis, gear_qualities, dust_qualities)
    return {'title': f'Récompense ajoutée au niveau {level.get('name')}',
            'description': f"Merci d'avoir ajouté une récompense à ce niveau! \nStatistiques actuelles pour ce niveau:\n{quantities_str}",
            'color': 'blue'}

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
    total_reward_appearances = sum([reward.get('appearances') for reward in rewards])
    quantities = []
    for r in rewards:
      icon = ''
      match r.get('type'):
        case 'gold':
          icon = ':moneybag:'
        case 'gear':
          icon = next((g.get('icon') for g in gear_qualities if g.get('name') == r.get('quality')), None)
        case 'dust':
          icon = next((d.get('icon') for d in dust_qualities if d.get('name') == r.get('quality')), None)
        case 'potions':
          icon = LevelService.get_potion_emoji(emojis)

      quantities.append(
        f"{icon} {r.get('quantity')} {r.get('quality', '')} {r.get('type')}: {format(r.get('appearances') / total_reward_appearances, '.2%')} ({r.get('appearances')})\n")

    return f'{total_reward_appearances} récompense{pluriel(total_reward_appearances)} recueillie{pluriel(total_reward_appearances)}:\n' + '\n'.join(
      [q for q in quantities])

  @staticmethod
  def get_potion_emoji(emojis):
    potion_emoji = discord.utils.get(emojis, name='potion')
    return str(potion_emoji) if potion_emoji else ''