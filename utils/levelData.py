import requests
from discord.app_commands import Choice

from config import DB_PATH

class LevelData:
  def __init__(self):
    self.known_levels = None

  def load(self):
    self.load_levels()

  def load_levels(self):
    try:
      response = requests.get(DB_PATH + 'levels')
      levels = response.json()
      self.known_levels = [Choice(name=l.get('name'), value=l.get('name')) for l in levels]

    except requests.RequestException as e:
      print(f"Erreur lors de la récupération des levels: {e}")
