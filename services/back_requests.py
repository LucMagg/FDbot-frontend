import requests
import json, os
from functools import lru_cache
from requests.exceptions import RequestException

from config import DB_PATH
from utils.str_utils import str_to_slug, slug_to_str


class BackRequests:
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger

  @lru_cache(maxsize=None)
  def load_requests(self):
    json_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils', 'all_requests.json')
    try:
      with open(json_file, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
      return json_data
    except Exception as e:
      self.logger.log_only('error', f'[BR] Failed loading all_requests.json : {e}')
  
  async def call(self, whichone, params=None):
    all_requests = self.load_requests()
    my_request = next((r for r in all_requests if r.get('name') == whichone), None)

    if my_request is None:
      self.logger.log_only('error', f'[BR] No request {whichone} found')
      return None
    
    url = self.build_url(my_request, params)
    self.logger.log_only('debug', f'[BR] Request : {my_request.get('name')} | url built : {url.get('url')}')
    try:
      match my_request.get('type'):
        case 'get':
          if url.get('has_json_in_params') is not None:
            self.logger.log_only('debug', f'[BR] json : {params[url.get('has_json_in_params')]}')
            response = requests.get(url.get('url'), json=params[url.get('has_json_in_params')])
          else:
            response = requests.get(url.get('url'))
        case 'post':
          if url.get('has_json_in_params') is not None:
            self.logger.log_only('debug', f'[BR] json : {params[url.get('has_json_in_params')]}')
            response = requests.post(url.get('url'), json=params[url.get('has_json_in_params')])
          else:
            response = requests.post(url.get('url'))
        case 'put':
          if url.get('has_json_in_params') is not None:
            self.logger.log_only('debug', f'[BR] json : {params[url.get('has_json_in_params')]}')
            response = requests.put(url.get('url'), json=params[url.get('has_json_in_params')])
          else:
            response = requests.put(url.get('url'))
        case 'delete':
          if url.get('has_json_in_params') is not None:
            self.logger.log_only('debug', f'[BR] json : {params[url.get('has_json_in_params')]}')
            response = requests.delete(url.get('url'), json=params[url.get('has_json_in_params')])
          else:
            response = requests.delete(url.get('url'))

      match response.status_code:
        case 200 | 201:
          self.logger.log_only('debug', f'[BR] Backend answer : {response.status_code}')
          return response.json()
        case 404:
          self.logger.log_only('debug', f'[BR] Backend answer : {response.status_code}')
          return response.json()
        case _:
          self.logger.log_only('error', f'[BR] Backend answer : {response.status_code} | Erreur : {response}')
          return False

    except RequestException as e:
      self.logger.log_only('error', f'[BR] Request error : {str(e)}')
      return False

  def build_url(self, my_request, params):
    to_return = my_request.get('url')
    nb_params = len([key for key in my_request if key.startswith('param')])
    
    has_json_in_params = None
    for i in range(0, nb_params):
      to_replace = False
      match my_request.get(f'param{i}'):
        case 'str':
          to_replace = slug_to_str(params[i])
        case 'slug':
          to_replace = str_to_slug(params[i])
        case 'json':
          has_json_in_params = i
        case 'default':
          to_replace = params[i]
      if to_replace:
        to_return = to_return.replace(f'[[param{i}]]', to_replace)
    to_return = f'{DB_PATH}{to_return}'
    
    return {'url': to_return, 'has_json_in_params': has_json_in_params}