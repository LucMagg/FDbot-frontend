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
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.error_msg = Message(bot).message('error')


  @lru_cache(maxsize=None)
  def load_requests(self):
    json_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils', 'all_requests.json')
    try:
      with open(json_file, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
      return json_data
    except Exception as e:
      self.logger.log_only('error', f'Problème de chargement du all_requests.json : {e}')
  
  async def call(self, whichone, handle_errors, params=None, interaction=None):
    all_requests = self.load_requests()
    my_request = next((r for r in all_requests if r.get('name') == whichone), None)

    if my_request is None:
      self.logger.error_log(f"Erreur! Il n'existe aucune requête {whichone}")
      return None
    
    url = self.build_url(my_request, params)
    self.logger.log_only('debug', f"requête : {my_request.get('name')} | url construite : {url.get('url')}")
    try:
      match my_request.get('type'):
        case 'get':
          response = requests.get(url.get('url'))
        case 'post':
          if url.get('has_json_in_params') is not None:
            response = requests.post(url.get('url'), json=params[url.get('has_json_in_params')])
          else:
            response = requests.post(url.get('url'))

      is_ok = await self.error_handler(my_request, response, handle_errors, params, interaction)

      if is_ok:
        return response.json()
      return False

    except RequestException as e:
      self.logger.error_log(f"Une erreur s'est produite lors de la requête : {e}")
      if interaction:
          error_response = {'title': 'Erreur', 'description': f'Une erreur s\'est produite : {str(e)}', 'color': 'red'}
          await self.send_message.update(interaction, error_response)
      return False

  def build_url(self, my_request, params):
    to_return = my_request.get('url')
    nb_params = len([key for key in my_request if key.startswith('param')])
    
    has_json_in_params = None
    for i in range(0, nb_params):
      to_replace = False
      match my_request.get(f"param{i}"):
        case "str":
          to_replace = slug_to_str(params[i])
        case "slug":
          to_replace = str_to_slug(params[i])
        case "json":
          has_json_in_params = i
        case "default":
          to_replace = params[i]
      if to_replace:
        to_return = to_return.replace(f"[[param{i}]]", to_replace)
    to_return = f"{DB_PATH}{to_return}"
    
    return {'url': to_return, 'has_json_in_params': has_json_in_params}
  
  async def error_handler(self, my_request, response, handle_errors, params, interaction):
    match response.status_code:
      case 200 | 201:
        self.logger.log_only('debug', f"Réponse du back-end : {response.status_code}")
        return True
      case 404:
        self.logger.log_only('debug', f"Réponse du back-end : {response.status_code}")
        if handle_errors:
          param = ' '.join(params)
          whichone = my_request.get('command')
          description = f"{self.error_msg.get('description').get(whichone)[0].get('text')} {param} {self.error_msg.get('description').get(whichone)[1].get('text')}"
          response = {'title': self.error_msg['title'], 'description': description, 'color': self.error_msg['color']}
          await self.send_message.update(interaction, response)
        return False
      case 500:
        self.logger.log_only('error', f"Réponse du back-end : {response.status_code}")
        if interaction:
          response = {'title': 'Erreur', 'description': 'La partie backend ne répond plus <@553925318683918336> :cry:', 'color': 'red'}
          await self.send_message.update(interaction, response)
        else:
          self.logger.error_log(f"Erreur du back : {response.json()}")
        return False