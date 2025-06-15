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
  async def mercask_app_command(self, interaction: discord.Interaction, héros: str, ascend: str|None = None, pet: str|None = None):
    self.logger.command_log('mercask', interaction)
    self.interaction_handler = InteractionHandler(self.bot)
    await self.interaction_handler.send_wait_message(interaction=interaction)
    response = await self.get_response(nick(interaction), interaction.user.id, héros, ascend, pet)
    if response:
      await self.interaction_handler.send_embed(interaction=interaction, response=response)
    self.logger.ok_log('mercask')

  async def get_response(self, user_name, user_id, hero, ascend, has_pet):
    if has_pet == 'Non':
      has_pet = False
    if has_pet == 'Oui':
      has_pet = True
    print(f'username: {user_name} / user_id: {user_id} / hero: {hero} / ascend: {ascend} / pet: {has_pet}')
    user_list = await self.get_users_by_merc(user_name, user_id, hero, ascend, has_pet)
      
    if user_list:
      hero = await self.bot.back_requests.call('getHeroByName', False, [str_to_slug(hero)])
      if hero:
        return {'title': '', 'description': user_list, 'color': hero.get('color')}
      return user_list
    return {'title': '', 'description': 'Une erreur s\'est produite lors de l\'envoi de la commande :shrug:\nMerci de réitérer la commande :wink:', 'color': 'red'}
  
  async def get_users_by_merc(self, user_name, user_id, hero, ascend, has_pet):
    found_hero = any(str_to_slug(hero) == str_to_slug(m.value) for m in self.choices)
    print(f'found_hero : {found_hero}')
    if not found_hero:
      return {'title': '', 'description': 'Le héros demandé n\'est pas recensé dans la liste des mercenaires disponibles :shrug:\nMerci de réitérer la commande :wink:', 'color': 'red'}
    
    user_list = await self.find_users(hero, ascend, has_pet)
    if not user_list:
      user_list = []

      found_users = await self.find_users(hero, None, has_pet)
      if found_users:
        user_list = found_users
        print(f'user_list: {user_list}')

      found_users = await self.find_users(hero, ascend, None)
      if found_users:
        user_list = list(set(found_users + user_list))

      header = f'Le héros {hero} n\'est pas disponible'
      if ascend:
        header += f' {ascend}'
      if has_pet:
        header += ' avec son pet'
      header += '.\n'

      user_list = [i for i in user_list if i.get('user_id') != user_id]      
      if len(user_list) > 0:
        return self.print_user_list(user_list, user_name, hero, header)
      else:
        return f'Personne d\'autre que toi ne possède {hero} dans les mercenaires recensés, désolé :shrug:'
    
    user_list = [i for i in user_list if i.get('user_id') != user_id]      
    if len(user_list) > 0:
      return self.print_user_list(user_list, user_name, hero)
    else:
      return f'Personne d\'autre que toi ne possède {hero} dans les mercenaires recensés, désolé :shrug:'
  
  async def find_users(self, hero, ascend, has_pet):
    to_find = {'merc': {'name': hero}}
    if ascend is not None:
      to_find['merc']['ascend'] = ascend
    if has_pet is not None:
      to_find['merc']['pet'] = has_pet
    return await self.bot.back_requests.call('getMerc', False, [to_find])
  
  def print_user_list(self, found_users, user_name, hero, optional_header = ''):
    description = optional_header
    for user in found_users:
      description += f'<@{user.get('user_id')}> '
    description += f' si possible, merci de mettre {hero} en mercenaire pour {user_name}, merci pour lui :wink:'
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