import discord
import typing
from discord.ext import commands
from discord import app_commands

from service.interaction_handler import InteractionHandler
from service.command import CommandService

from utils.misc_utils import nick
from utils.str_utils import str_to_slug


class Mercask(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'mercask'), None)
    self.xp_data = bot.static_data.xp_data
    self.thresholds = bot.static_data.xp_thresholds
    self.ascends = None

    CommandService.init_command(self.mercask_app_command, self.command)
    self.choices = None

  async def héros_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await CommandService.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(héros=héros_autocomplete)
  @app_commands.command(name='mercask')
  async def mercask_app_command(self, interaction: discord.Interaction, héros: str):
    self.logger.command_log('mercask', interaction)
    self.interaction_handler = InteractionHandler(self.bot)
    await self.interaction_handler.send_wait_message(interaction=interaction)
    response = await self.get_response(nick(interaction), interaction.user.id, héros)
    if response:
      await self.interaction_handler.send_embed(interaction=interaction, response=response)
    self.logger.ok_log('mercask')

  async def get_response(self, user_name, user_id, hero):
    print(f'username: {user_name} / user_id: {user_id} / hero: {hero}')
    user_list = await self.get_users_by_merc(user_name, user_id, hero)
    if user_list:
      hero = await self.bot.back_requests.call('getHeroByName', False, [str_to_slug(hero)])
      if hero:
        return {'title': '', 'description': user_list, 'color': hero.get('color')}
      return user_list
    return {'title': '', 'description': 'Une erreur s\'est produite lors de l\'envoi de la commande :shrug:\nMerci de réitérer la commande :wink:', 'color': 'red'}
  
  async def get_users_by_merc(self, user_name, user_id, hero):
    found_hero = any(str_to_slug(hero) == str_to_slug(m.value) for m in self.choices)
    print(f'found_hero : {found_hero}')
    if not found_hero:
      return {'title': '', 'description': 'Le héros demandé n\'est pas recensé dans la liste des mercenaires disponibles :shrug:\nMerci de réitérer la commande :wink:', 'color': 'red'}
    
    to_find = {'merc': {'name': hero}}
    print(f'to_find: {to_find}')
    user_list = await self.bot.back_requests.call('getMerc', False, [to_find])
    if not user_list:
      return None
    user_list = [i for i in user_list if i.get('user_id') != user_id]      
    if len(user_list) > 0:
      return self.print_user_list(user_list, user_name, hero)
    else:
      return f'Personne d\'autre que toi ne possède {hero} dans les mercenaires recensés, désolé :shrug:'
  
  def print_user_list(self, user_list, user_name, hero):
    description = f'# Besoin de {hero} pour {user_name} # \n'
    for user in user_list:
      print(user)
      if len(user_list) > 1:
        description += '- '
      description += f'<@{user.get('user_id')}>'
      merc = user.get('merc')
      if merc.get('a2_talent') or merc.get('a3_talent') or merc.get('ascend') or merc.get('merge') or merc.get('pet'):
        description += f'({self.bot.merc_service.print_merc_details(merc)})'
      description += '\n'
    description += 'Merci pour lui :kissing_heart:'
    return description
    
  async def setup(self, param_list):
    if param_list is None:
      choices = await self.bot.back_requests.call('getAllUniqueMercs', False)
      if not choices:
        choices = []
      else:
        choices = [{'name': c} for c in choices]
    else:
      choices = param_list
    self.choices = CommandService.set_choices(choices)

async def setup(bot):
  await bot.add_cog(Mercask(bot))