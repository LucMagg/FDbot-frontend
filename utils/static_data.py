import requests
from config import DB_PATH

class StaticData:
  def __init__(self):
    self.messages = None
    self.dusts = None
    self.qualities = None
    self.commands = None
    self.xpdata = None
    self.xp_thresholds = None

  def load_all_data(self):
    self.load_messages()
    self.load_dusts()
    self.load_qualities()
    self.load_commands()
    self.load_xpdata()
    self.load_xp_thresholds()

  def load_messages(self):
    try:
      response = requests.get(DB_PATH + 'message')
      self.messages = response.json()
    except requests.RequestException as e:
      print(f"Erreur lors de la récupération des messages: {e}")

  def get_messages(self):
    if self.messages is None:
      self.load_messages()
    return self.messages
  
  def load_dusts(self):
    try:
      response = requests.get(DB_PATH + 'dust')
      self.dusts = response.json()
    except requests.RequestException as e:
      print(f"Erreur lors de la récupération des dusts: {e}")

  def get_dusts(self):
    if self.dusts is None:
      self.load_dusts()
    return self.dusts
  
  def load_qualities(self):
    try:
      response = requests.get(DB_PATH + 'quality')
      self.qualities = response.json()
    except requests.RequestException as e:
      print(f"Erreur lors de la récupération des qualities: {e}")

  def get_qualities(self):
    if self.qualities is None:
      self.load_qualities()
    return self.qualities
  
  def load_commands(self):
    try:
      response = requests.get(DB_PATH + 'command')
      self.commands = response.json()
    except requests.RequestException as e:
      print(f"Erreur lors de la récupération des commands: {e}")

  def get_commands(self):
    if self.commands is None:
      self.load_commands()
    return self.commands
  
  def load_xpdata(self):
    try:
      response = requests.get(DB_PATH + 'heroXp')
      self.xpdata = response.json()
    except requests.RequestException as e:
      print(f"Erreur lors de la récupération des heroXp: {e}")

  def get_xpdata(self):
    if self.xpdata is None:
      self.load_xpdata()
    return self.xpdata
  
  def load_xp_thresholds(self):
    try:
      response = requests.get(DB_PATH + 'xpThresholds')
      self.xp_thresholds = response.json()
    except requests.RequestException as e:
      print(f"Erreur lors de la récupération des heroXp: {e}")

  def get_xp_thresholds(self):
    if self.xp_thresholds is None:
      self.load_xp_thresholds()
    return self.xp_thresholds