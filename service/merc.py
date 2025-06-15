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
      description += self.print_merc(heroes, merc)
    return {'title': '', 'description': description, 'color': 'blue'}
  
  def print_merc(self, heroes, merc):
    hero = next((h for h in heroes if h.get('name_slug') == merc.get('name_slug')), None)
    if hero :
      to_return = f'- {hero.get('name')}'
    else:
      to_return = f'{merc.get('name')}'

    if merc.get('ascend'):
      to_return += f' ({merc.get('ascend')}'
    
    if merc.get('pet'):
      if not merc.get('ascend'):
        to_return += ' (avec son pet'
      else:
        to_return += ' avec son pet'
    
    if merc.get('pet') or merc.get('ascend'):
      to_return += ')\n'
    else:
      to_return += '\n'
    return to_return