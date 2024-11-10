import discord
import typing
import math
from discord.ext import commands
from discord import app_commands

from utils.sendMessage import SendMessage
from utils.misc_utils import stars as stars_to_str
from service.command import CommandService


class Xp(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'xp'), None)
    self.xpdata = bot.static_data.xpdata
    self.thresholds = bot.static_data.xp_thresholds
    self.ascends = None

    self.command_service = CommandService()
    CommandService.init_command(self.xp_app_command, self.command)
    self.ascend_choices = None
    self.star_choices = None


  async def stars_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[int]]:
    return [c for c in self.star_choices if current in str(c.name)]

  async def ascend_choices_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return [c for c in self.ascend_choices if current.lower() in c.name.lower()]
  

  @app_commands.autocomplete(stars=stars_autocomplete)
  @app_commands.autocomplete(current_ascend=ascend_choices_autocomplete)
  @app_commands.autocomplete(target_ascend=ascend_choices_autocomplete)
  @app_commands.command(name='xp')
  async def xp_app_command(self, interaction: discord.Interaction, stars: int, current_ascend: str, current_level: int, target_ascend: str, target_level: int):
    self.logger.command_log('xp', interaction)
    await self.send_message.handle_response(interaction=interaction, wait_msg=True)
    response = await self.get_response(stars, current_ascend, current_level, target_ascend, target_level)
    if response:
      await self.send_message.handle_response(interaction=interaction, response=response)
    self.logger.ok_log('xp')

  async def get_response(self, stars, current_ascend, current_level, target_ascend, target_level):
    if stars not in [s.name for s in self.star_choices]:
      return {'title': 'Erreur', 'description': f'{stars} n\'est pas un nombre d\'étoiles valide pour un héro :wink:', 'color': 'red'}

    
    self.xp_table = next((d.get('data') for d in self.xpdata if d.get('hero_stars') == stars), None)
    self.threshold_table = next((d for d in self.thresholds if d.get('hero_stars') == stars), None)
    
    
    is_a_valid_request = self.check_errors(stars, current_ascend, current_level, target_ascend, target_level)
    if is_a_valid_request is not True:
      return is_a_valid_request
    
    description = f'# {stars_to_str(stars)} #\n'
    description += self.calc_xp(stars, current_ascend, current_level, target_ascend, target_level)

    return {'title': '', 'description': description, 'color': 'blue'}

  def calc_xp(self, stars, current_ascend, current_level, target_ascend, target_level):
    initial_return = f' potions d\'xp pour passer un héros {stars}* de {current_ascend} niveau {current_level} à {target_ascend} niveau {target_level}'
    
    current_potions = 0
    total_potions = 0
    is_calc_done = False

    calc_return = ''
    if self.threshold_table.get(current_ascend).get('threshold') is not None:
      if current_level >= self.threshold_table.get(current_ascend).get('threshold'):
        current_level = math.ceil(current_level/2)
        current_ascend = self.ascends[self.ascends.index(current_ascend) + 1]
        calc_return = f'- passer directement {current_ascend}\n'
    
    while not is_calc_done:
      current_level += 1
      potions_to_add = next((xp.get(current_ascend) for xp in self.xp_table if xp.get('level') == current_level), None)
      if potions_to_add is not None:
        current_potions += potions_to_add

      if current_ascend != target_ascend:
        if current_level == self.threshold_table.get(current_ascend).get('threshold'):
          calc_return += f'- utiliser {current_potions} potions d\'xp jusqu\'à {current_ascend} niveau {current_level}\n'
          current_level = math.ceil(current_level/2)
          current_ascend = self.ascends[self.ascends.index(current_ascend) + 1]
          calc_return += f'- ascend {current_ascend}\n'
          total_potions += current_potions
          current_potions = 0

      if current_level == target_level and current_ascend == target_ascend:
        is_calc_done = True

    if calc_return != '':
      calc_return += f'- utiliser {current_potions} potions d\'xp jusqu\'à {current_ascend} niveau {current_level}\n'
      optional_return = ', en suivant ce cheminement :\n'
    else:
      optional_return = '.'
    total_potions += current_potions

    return f'Il faut {total_potions}{initial_return}{optional_return}{calc_return}'


  def check_errors(self, stars, current_ascend, current_level, target_ascend, target_level):
    if current_ascend not in [c.name for c in self.ascend_choices] or target_ascend not in [c.name for c in self.ascend_choices]:
      return {'title': 'Erreur', 'description': 'Merci de choisir une ascension valide parmi celles proposées :rolling_eyes:', 'color': 'red'}
   
    check_current = self.check_level_consistency(stars, current_ascend, current_level)
    if not check_current.get('valid'):
      return check_current.get('error_response')
    
    check_target = self.check_level_consistency(stars, target_ascend, target_level)
    if not check_target.get('valid'):
      return check_target.get('error_response')
    
    if current_ascend == target_ascend and current_level == target_level:
      return {'title': 'Requête stupide :wink:', 'description': 'Pour garder le même level, le héros n\'a pas besoin de potions d\'xp :shrug:', 'color': 'red'}
    
    exceptions = [f'Pour passer de {current_ascend} niveau {current_level} à {target_ascend} niveau {target_level}, il suffit d\'ascend le héros, pas besoin de potions d\'xp :shrug:',
                  f'Il n\'est pas possible pour un héros de passer de {current_ascend} niveau {current_level} à {target_ascend} niveau {target_level}, étant donné qu\'après ascension il sera déjà ']
    if current_ascend != target_ascend:
      if current_level >= self.threshold_table.get(current_ascend).get('threshold'):
        current_level = math.ceil(current_level/2)
        current_ascend = self.ascends[self.ascends.index(current_ascend) + 1]
      if current_ascend == target_ascend and current_level == target_level:
        return {'title': 'Requête stupide :wink:', 'description': exceptions[0], 'color': 'red'}
      if current_ascend == target_ascend and current_level > target_level:
        return {'title': 'Requête stupide :wink:', 'description': f'{exceptions[1]} {current_ascend} niveau {current_level} :shrug:', 'color': 'red'}

    if int(current_ascend[1]) > int(target_ascend[1]):
      return {'title': 'Erreur', 'description': 'Il n\'est pas possible pour un héros de baisser son niveau d\'ascension :shrug:', 'color': 'red'}
    
    if int(current_ascend[1]) == int(target_ascend[1]) and current_level > target_level:
      return {'title': 'Erreur', 'description': 'Il n\'est pas possible pour un héros de baisser de niveau :shrug:', 'color': 'red'}

    return True

  def check_level_consistency(self, stars, ascend, level):
    threshold_data = self.threshold_table.get(ascend)
    if level < threshold_data.get('level').get('min') or level > threshold_data.get('level').get('max'):
      return {'valid': False, 'error_response': {'title': 'Erreur', 'description': f'Il est impossible pour un héros {stars}* d\'être level {level} avec une ascension {ascend}.\nMerci de vérifier et de réitérer la commande :rolling_eyes:', 'color': 'red'}}
    return {'valid': True}

  def calc_ascend_choices(self):
    self.ascends = list(self.xpdata[0].get('data')[0].keys())
    self.ascends.remove('level')
    choices = [app_commands.Choice(name=a, value=a) for a in self.ascends]
    return choices
  
  def calc_star_choices(self, heroes):
    to_return = []
    for h in heroes:
      if h.get('stars') not in to_return:
        to_return.append(h.get('stars'))
    return [app_commands.Choice(name=s, value=s) for s in sorted(to_return)]
    
  async def setup(self, param_list):
    if param_list is None:
      heroes = await self.bot.back_requests.call('getAllHeroes', False)
    else:
      heroes = param_list
    self.star_choices = self.calc_star_choices(heroes)
    self.ascend_choices = self.calc_ascend_choices()
  
async def setup(bot):
  await bot.add_cog(Xp(bot))