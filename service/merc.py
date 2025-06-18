from utils.misc_utils import stars


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
    description = f'# Liste des mercs de {user_doc.get('user')} : # \n'
    mercs = sorted(user_doc.get('mercs'), key=lambda x: x['name'])
    for merc in mercs:
      hero = next((h for h in heroes if h.get('name_slug') == merc.get('name_slug')), None)
      description += f'- {hero.get('name') if hero else merc.get('name')}'
      details = self.print_merc_details(merc)
      if details != '':
        description += f' ({details})'
      description += '\n'
    return {'title': '', 'description': description, 'color': 'blue'}
  
  def print_merc_details(self, merc):
    to_return = ' '
    if merc.get('ascend'):
      to_return += f'{merc.get('ascend')} '
    if merc.get('merge'):
      to_return += f'M{merc.get('merge')} '
    if merc.get('pet'):
      to_return += f'avec son pet '
    if (merc.get('talent_a2') and merc.get('ascend') != 'A3') or merc.get('talent_a3'):
      if merc.get('pet'):
        to_return += 'et '
      else:
        to_return += 'avec '
      if merc.get('talent_a3'):
        to_return += 'son talent A3 '
      else:
        to_return += 'son talent A2 '
    return to_return.strip()