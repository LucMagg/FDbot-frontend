import requests
from config import DB_PATH

class BackRequests:
  def __init__(self):
    self.back_url = DB_PATH

  @classmethod
  def get(self, whichone):
    print(self.back_url + whichone)
    response = requests.get(self.back_url + whichone)
    return response
  
  @classmethod
  def post(self, whichone):
    response = requests.post(self.back_url + whichone)
    return response