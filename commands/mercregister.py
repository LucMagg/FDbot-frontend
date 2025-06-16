import discord
import typing
from discord.ext import commands
from discord import app_commands

from service.interaction_handler import InteractionHandler
from service.command import CommandService

from utils.misc_utils import nick
from utils.str_utils import str_to_slug


class Mercregister(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'mercregister'), None)
    self.xp_data = bot.static_data.xp_data
    self.thresholds = bot.static_data.xp_thresholds
    self.ascends = None

    CommandService.init_command(self.mercregister_app_command, self.command)
    self.choices = None

  async def héros_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await CommandService.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(héros=héros_autocomplete)
  @app_commands.command(name='mercregister')
  async def mercregister_app_command(self, interaction: discord.Interaction, héros: str, ascend: str|None = None, pet: str|None = None, talent_a2: str|None = None, talent_a3: str|None = None, merge: str|None = None):
    self.logger.command_log('mercregister', interaction)
    self.interaction_handler = InteractionHandler(self.bot)
    await self.interaction_handler.send_wait_message(interaction=interaction)
    response = await self.get_response(nick(interaction), interaction.user.id, héros, ascend, pet, talent_a2, talent_a3, merge)
    if response:
      await self.interaction_handler.send_embed(interaction=interaction, response=response)
    self.logger.ok_log('mercregister')

  async def get_response(self, user_name, user_id, hero, ascend, has_pet, talent_a2, talent_a3, merge):
    if has_pet == 'Non':
      has_pet = False
    if has_pet == 'Oui':
      has_pet = True
    if talent_a2 == 'Non':
      talent_a2 = False
    if talent_a2 == 'Oui':
      talent_a2 = True
    if talent_a3 == 'Non':
      talent_a3 = False
    if talent_a3 == 'Oui':
      talent_a3 = True
    print(f'username: {user_name} / user_id: {user_id} / hero: {hero} / ascend: {ascend} / pet: {has_pet} / talent_a2: {talent_a2} / talent_a3: {talent_a3} / merge: {merge} ')
    user = await self.add_merc_to_user(user_name, user_id, hero, ascend, has_pet, talent_a2, talent_a3, merge)
    if user:
      merclist_cog = self.bot.get_cog('Merclist')
      if merclist_cog:
        await merclist_cog.setup(None)
      mercask_cog = self.bot.get_cog('Mercask')
      if mercask_cog:
        await mercask_cog.setup(None)
      return await self.bot.merc_service.send_mercs_embed(user)
    return {'title': '', 'description': 'Une erreur s\'est produite lors de l\'envoi de la commande :shrug:\nMerci de réitérer la commande :wink:', 'color': 'red'}
  
  async def add_merc_to_user(self, user_name, user_id, hero, ascend, has_pet, talent_a2, talent_a3, merge):
    found_hero = await self.bot.back_requests.call('getHeroByName', False, [str_to_slug(hero)])
    if not found_hero:
      return None
    to_add = {
      'user': user_name,
      'user_id': user_id,
      'mercs': [{
        'name': found_hero.get('name'),
        'name_slug': found_hero.get('name_slug')
      }]
    }
    if ascend is not None:
      to_add['mercs'][0]['ascend'] = ascend
    if has_pet is not None:
      to_add['mercs'][0]['pet'] = has_pet
    if talent_a2 is not None:
      to_add['mercs'][0]['talent_a2'] = talent_a2
    if ascend == 'A3':
      to_add['mercs'][0]['talent_a2'] = True
    if talent_a3 is not None:
      to_add['mercs'][0]['talent_a3'] = talent_a3
    if merge is not None:
      to_add['mercs'][0]['merge'] = merge
    print(to_add)
    return await self.bot.back_requests.call('addMerc', False, [to_add])
    
  async def setup(self, param_list):
    if param_list is None:
      choices = await self.bot.back_requests.call('getAllHeroes', False)
    else:
      choices = param_list
    self.choices = CommandService.set_choices(choices)

async def setup(bot):
  await bot.add_cog(Mercregister(bot))