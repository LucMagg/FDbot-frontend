from typing import Optional

import requests

from config import DB_PATH


class LevelService:

  @staticmethod
  def create_level(name, cost):
    data = {
      "name": name,
      "cost": cost
    }
    return requests.post(f"{DB_PATH}levels", json=data).json()

  @staticmethod
  def add_reward(level_name, reward_type, reward_quantity, reward_quality: Optional[str]= ''):
    data = {
      "type": reward_type,
      "quantity": reward_quantity,
      "quality": reward_quality
    }
    return requests.post(f"{DB_PATH}levels/{level_name}/reward", json=data).json()

  @staticmethod
  def get_levels():
    return requests.get(f"{DB_PATH}levels").json()

  @staticmethod
  def get_level(level_name):
    return requests.get(f"{DB_PATH}levels/{level_name}").json()

  @staticmethod
  def get_rewards_str(rewards):
    total_reward_appearances = sum([reward.get('appearances') for reward  in rewards])
    quantities = [
      f"{r.get('quantity')} {r.get('quality', '')} {r.get('type')}: {format(r.get('appearances') / total_reward_appearances, '.2%')}\n"
      for r in rewards]
    return '\n'.join([q for q in quantities])

  @staticmethod
  def get_gear_qualities():
    return requests.get(f"{DB_PATH}quality/gears").json()

  @staticmethod
  def get_dust():
    return requests.get(f"{DB_PATH}dust").json()

