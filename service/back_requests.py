import requests
import json, os
from functools import lru_cache
from requests.exceptions import RequestException

from config import DB_PATH
from utils.str_utils import str_to_slug, slug_to_str
from utils.sendMessage import SendMessage
from utils.message import Message


class BackRequests:
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.error_msg = Message(bot).message('error')


  @staticmethod
  @lru_cache(maxsize=None)
  def load_requests():
    json_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils', 'all_requests.json')
    with open(json_file, 'r', encoding='utf-8') as file:
      json_data = json.load(file)
    return json_data
  
  async def call(self, whichone, handle_errors, params=None, interaction=None):
    all_requests = BackRequests.load_requests()
    my_request = next((r for r in all_requests if r.get('name') == whichone), None)

    if my_request is None:
      print(f"Erreur! Il n'existe aucune requête {whichone}")
      return None
    
    url = self.build_url(my_request, params)
    try:
      match my_request.get('type'):
        case 'get':
          response = requests.get(url.get('url'))
        case 'post':
          if url.get('has_json_in_params'):
            response = requests.post(url.get('url'), json=params)
          else:
            response = requests.post(url.get('url'))

      is_ok = await self.error_handler(my_request, response, handle_errors, params, interaction)

      if is_ok:
        return response.json()
      return False

    except RequestException as e:
      print(f"Une erreur s'est produite lors de la requête : {e}")
      if interaction:
          error_response = {'title': 'Erreur', 'description': f'Une erreur s\'est produite : {str(e)}', 'color': 'red'}
          await self.send_message.update(interaction, error_response)
      return False

  def build_url(self, my_request, params):
    to_return = my_request.get('url')
    nb_params = to_return.count('[[param')
    has_json_in_params = False
    
    for i in range(0, nb_params):
      match my_request.get(f"param{i}"):
        case "str":
          to_replace = slug_to_str(params[i])
        case "slug":
          to_replace = str_to_slug(params[i])
        case "default":
          to_replace = params[i]
        case "json":
          has_json_in_params = True
          break
      to_return = to_return.replace(f"[[param{i}]]", to_replace)

    to_return = f"{DB_PATH}{to_return}"
    return {'url': to_return, 'has_json_in_params': has_json_in_params}
  
  async def error_handler(self, my_request, response, handle_errors, params, interaction):
    match response.status_code:
      case 200 | 201:
        return True
      case 404:
        if handle_errors:
          param = ' '.join(params)
          whichone = my_request.get('command')
          description = f"{self.error_msg.get('description').get(whichone)[0].get('text')} {param} {self.error_msg.get('description').get(whichone)[1].get('text')}"
          response = {'title': self.error_msg['title'], 'description': description, 'color': self.error_msg['color']}
          await self.send_message.update(interaction, response)
        return False
      case 500:
        if interaction:
          response = {'title': 'Erreur', 'description': 'La partie backend ne répond plus <@553925318683918336> :cry:', 'color': 'red'}
          await self.send_message.update(interaction, response)
        else:
          print(f"Erreur du back : {response.json()}")
        return False