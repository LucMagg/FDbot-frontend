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
  def add_reward(level_name, reward_type, reward_quantity):
    data = {
      "type": reward_type,
      "quantity": reward_quantity
    }
    return requests.post(f"{DB_PATH}levels/{level_name}/reward", json=data).json()

  @staticmethod
  def get_levels():
    return requests.get(f"{DB_PATH}levels").json()

  @staticmethod
  def get_level(level_name):
    return requests.get(f"{DB_PATH}levels/{level_name}").json()

