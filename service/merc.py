from utils.misc_utils import stars
from collections import defaultdict

class MercService:
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger

  async def get_all_mercs_by_user_id(self, user_id):
    if isinstance(user_id, str):
      user_id = int(user_id)
    user_doc = await self.bot.back_requests.call('getAllMercsByUser', False, [{"user": user_id}])
    if not user_doc:
      return {'title': '', 'description': 'L\'utilisateur n\'a pas été trouvé :shrug:\nMerci de vérifier et de réitérer la commande :wink:', 'color': 'red'}
    return await self.send_mercs_embed(user_doc)
  
  async def send_mercs_embed(self, user_doc):
    if not user_doc:
      return None
    heroes = await self.bot.back_requests.call('getAllHeroes', False)
    if not heroes:
      return {'title': '', 'description': 'Une erreur s\'est produite lors de l\'envoi de la commande :shrug:\nMerci de réitérer la commande :wink:', 'color': 'red'}
    descriptions = [f'# Liste des mercs de {user_doc.get('user')} : #']
    mercs = sorted(user_doc.get('mercs'), key=lambda x: x['name'])
    mercH = [h for h in heroes if h.get('name_slug') in [m['name_slug'] for m in mercs]]

    mercHByColor = defaultdict(list)
    for h in mercH:
      key = h['color']
      mercHByColor[key].append(h)

    for color, colorHeroes in mercHByColor.items():
      descriptions.append(self.print_color_merc_details(color, mercs, colorHeroes))

    return {'title': '', 'description': '\n'.join(descriptions), 'color': 'blue'}

  def print_color_merc_details(self, color, mercs, mercsH):
    to_return = f'## {color} ##\n'
    details = []
    for merc in mercs:
      hero = next((h for h in mercsH if h.get('name_slug') == merc.get('name_slug')), None)
      if not hero:
        continue
      details.append(self.print_merc_details(merc, hero))

    to_return += '\n'.join(details)
    return to_return

  def print_merc_details(self, merc, hero):
    name = f'- {hero.get('name') if hero else merc.get('name')}'
    details = ''
    if merc.get('ascend'):
      details += f'{merc.get('ascend')} '
    if merc.get('merge'):
      details += f'M{merc.get('merge')} '
    if merc.get('pet'):
      details += f'avec son pet '
    if (merc.get('talent_a2') and merc.get('ascend') != 'A3') or merc.get('talent_a3'):
      if merc.get('pet'):
        details += 'et '
      else:
        details += 'avec '
      if merc.get('talent_a3'):
        details += 'son talent A3 '
      else:
        details += 'son talent A2 '
    if not details:
      return name
    return f'{name} ({details.strip()})'