import discord

from utils.misc_utils import pluriel
from utils.str_utils import str_to_slug, int_to_str
from collections import defaultdict


class LevelService:
  def __init__(self, bot):
    self.bot = bot
    self.gear_qualities = [g for g in bot.static_data.qualities if g['type'] == 'gear']
    self.dust_qualities = bot.static_data.dusts

  async def display_rewards(self, emojis, level_name):
    level = await self.bot.back_requests.call('getLevelByName', False, [level_name])
    description = f'# {level.get('name')} #\n'
    description += self.get_rewards_str(level, emojis)

    print(description)
    
    return {'title': '', 'description': description, 'color': 'blue'}

  async def add_reward(self, emojis, level_name, reward_data: dict):
    level = await self.bot.back_requests.call('addReward', False, [str_to_slug(level_name), reward_data])
    print('here')

    description = f'# {level.get('name')} #\n'
    description += 'Merci d\'avoir ajouté une récompense à ce niveau ! :kissing_heart:\n\n'
    description += self.get_rewards_str(level, emojis)

    return {'title': '', 'description': description, 'color': 'blue'}

  def get_rewards_str(self, level, emojis) -> str:
    self.total_appearances = sum([r.get('total_appearances') for r in level.get('rewards')])
    print(self.total_appearances)

    to_return = ''
    for r in level.get('rewards'):
      if r.get('quality') == None:
        icon = next((rc.get('icon') for rc in level.get('reward_choices') if rc.get('name') == r.get('type')), '')
      else:
        try:
          match_reward_type = next((rc for rc in level.get('reward_choices') if rc.get('name') == r.get('type')), '')
          match_quality = next((rc for rc in match_reward_type.get('choices') if rc.get('name') == 'Quality'), '')
          icon = next((rc.get('icon') for rc in match_quality.get('choices') if rc.get('name') == r.get('quality')), '')
        except:
          icon = ''
      print('here')
      icon = self.get_custom_emoji(emojis, icon)
      
      
      if len(level.get('rewards')) > 1:
        to_return += self.append_with_multiple_reward_types(r, icon)
      else:
        to_return += self.append_with_single_reward_type(level, r, icon)
      
      print(to_return)
   
    return f'### Statistiques actuelles sur {self.total_appearances} récompense{pluriel(self.total_appearances)} recueillie{pluriel(self.total_appearances)} : ###\n{to_return}'
  
  def append_with_multiple_reward_types(self, reward, icon):
    print('multiple rewards types')
    to_return = f"\n{icon} {reward.get('quality')} {reward.get('type')} : {format(reward.get('total_appearances') / self.total_appearances, '.2%')} ({reward.get('total_appearances')}), soit :\n"
    for d in reward.get('details'):
      to_return += '\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0• '
      if d.get('item') is not None:
        to_return += f'{d.get('item')} '
      else:
        quantity = int_to_str(d.get('quantity'))
        to_return += f'{quantity} {reward.get('type')} '
      to_return += f'{format(d.get('appearances') / reward.get('total_appearances'), '.2%')} ({d.get('appearances')})\n'
    return to_return
  
  def append_with_single_reward_type(self, level, reward, icon):
    print('single reward type')
    to_return = ''
    has_quantity = False
    for d in reward.get('details'):
      if reward.get('quality') is not None:
        type = f'{reward.get('quality')} {reward.get('type')}'
      else:
        type = reward.get('type')
      if d.get('quantity') is not None:
        quantity = int_to_str(d.get('quantity'))
        has_quantity = True
      else:
        quantity = ''

      to_return += f'\n{icon} {quantity} {type} : {format(d.get('appearances') / self.total_appearances, '.2%')} ({d.get('appearances')})\n'
    
    if has_quantity:
      to_return += self.energy_stats(level, reward, icon)
    print(to_return)
    return to_return
 
  def get_custom_emoji(self, emojis, icon):
    print('get emoji')
    if not 'customIcon' in icon:
      return icon
    
    icon = icon.split(':')[1]
    print(f'iconsplit : {icon}')
    try:
      emoji = discord.utils.get(emojis, name=icon)
    except:
      emoji = ''
    return emoji
  
  def energy_stats(self, level, reward, icon):
    print(level)
    to_return = f'\n### Moyennes par combat : ###\n'

    total_rewards = sum([(d.get('quantity') * d.get('appearances')) for d in reward.get('details')])
    print(f'total_rewards: {total_rewards}')
    average_reward = total_rewards/self.total_appearances
    print(f'average: {average_reward}')

    to_return += f'{icon} {round(average_reward)} par combat, soit :\n'

    try:
      to_check = [{'attr': 'standard_energy_cost', 'name': 'énergie solo'},{'attr': 'coop_energy_cost', 'name': 'énergie coop'}]
      for energy in to_check:
        energy_cost = level.get(energy.get('attr'))
        if energy_cost is not None:
          to_return += f'\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0• {round(average_reward//energy_cost)} par {energy.get('name')} ({energy_cost} par combat)\n'
    except Exception as e:
      print(f'Erreur: {e}')

    return to_return