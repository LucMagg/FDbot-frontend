import discord
import typing
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

from utils.sendMessage import SendMessage
from service.command import CommandService


class Xp(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'xp'), None)
    self.xpdata = bot.static_data.xpdata

    self.command_service = CommandService()
    CommandService.init_command(self.xp_app_command, self.command)
    self.ascend_choices = None
    self.hero_choices = None


  async def héros_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    choices = await self.command_service.return_autocompletion(self.hero_choices, current)
    return choices

  async def ascend_choices_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return [c for c in self.ascend_choices if current.lower() in c.name.lower()]
  

  @app_commands.autocomplete(héros=héros_autocomplete)
  @app_commands.autocomplete(current_ascend=ascend_choices_autocomplete)
  @app_commands.autocomplete(target_ascend=ascend_choices_autocomplete)
  @app_commands.command(name='xp')
  async def xp_app_command(self, interaction: discord.Interaction, héros: str, current_ascend: str, current_level: int, target_ascend: str, target_level: int):
    self.logger.command_log('xp', interaction)
    await self.send_message.post(interaction)
    response = await self.get_response(interaction, héros, current_ascend, current_level, target_ascend, target_level)
    if response:
      await self.send_message.update(interaction, response)
    self.logger.ok_log('xp')

  async def get_response(self, interaction, hero_name, current_ascend, current_level, target_ascend, target_level):
    hero = await self.bot.back_requests.call('getHeroByName', True, [hero_name], interaction)
    if not hero:
      return False
    
    stars = hero.get('stars')
    self.xp_table = next((d for d in self.xpdata if d.get('hero_stars') == stars), None)
    self.xp_table = self.xp_table.get('data')
    
    if current_ascend not in [c.name for c in self.ascend_choices] or target_ascend not in [c.name for c in self.ascend_choices]:
      return {'title': 'Erreur', 'description': 'Merci de choisir une ascension valide parmi celles proposées :rolling_eyes:', 'color': 'red'}
    print('ascend ok')

    if current_level < 1 or current_level > 100 or target_level < 2 or target_level > 100:
      return {'title': 'Erreur', 'description': 'Merci de choisir un level valide :rolling_eyes:', 'color': 'red'}
    print('level ok')
    
    check_current = self.check_level_consistency(stars, current_ascend, current_level)
    if not check_current.get('valid'):
      return check_current.get('error_response')
    
    check_target = self.check_level_consistency(stars, target_ascend, target_level)
    if not check_target.get('valid'):
      return check_target.get('error_response')
    
    if current_ascend == target_ascend and current_level == target_level:
      return {'title': 'Requête stupide :wink:', 'description': 'Pour garder le même level, le héros n\'a pas besoin de potions d\'xp :shrug:', 'color': 'red'}

    return {'title': 'ok', 'description': 'ok', 'color': hero.get('color')}

  def check_level_consistency(self, stars, ascend, level):
    print('check')
    data = next((d for d in self.xp_table if d.get('level') == level), None)
    print(data)
    if data is None:
      return {'valid': False, 'error_response': {'title': 'Erreur', 'description': f'Le level {level} n\'a pas été trouvé dans la base des levels recensés.\nMerci de vérifier et de réitérer la commande :rolling_eyes:', 'color': 'red'}}
    if data.get(ascend) is None:
      return {'valid': False, 'error_response': {'title': 'Erreur', 'description': f'Il est impossible pour un héro d\'être level {level} avec une ascension {ascend}.\nMerci de vérifier et de réitérer la commande :rolling_eyes:', 'color': 'red'}}
    return {'valid': True}

  def calc_ascend_choices(self):
    ascend_list = ['A0','A1','A2','A3']
    choices = [app_commands.Choice(name=a, value=a) for a in ascend_list]
    return choices
    
  async def setup(self, param_list):
    if param_list is None:
      choices = await self.bot.back_requests.call('getAllHeroes', False)
    else:
      choices = param_list
    self.hero_choices = CommandService.set_choices(choices)
    self.ascend_choices = self.calc_ascend_choices()
  
async def setup(bot):
  await bot.add_cog(Xp(bot))