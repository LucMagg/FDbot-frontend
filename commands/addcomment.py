import discord
from discord.ext import commands
from discord import app_commands
import typing
from typing import Optional

from service.command import CommandService
from utils.message import Message
from service.interaction_handler import InteractionHandler
from utils.str_utils import str_to_slug
from utils.misc_utils import nick

from commands.hero import Hero
from commands.pet import Pet


class Addcomment(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.interaction_handler = InteractionHandler(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'addcomment'), None)
    self.error_msg = Message(bot).message('error')
    self.help_msg = Message(bot).help('addcomment')

    CommandService.init_command(self.addcomment_app_command, self.command)
    self.choices = None

  async def héros_ou_pet_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await CommandService.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(héros_ou_pet=héros_ou_pet_autocomplete)
  @app_commands.command(name='addcomment')
  async def addcomment_app_command(self, interaction: discord.Interaction, héros_ou_pet: str, commentaire: Optional[str] = None):
    self.logger.command_log('addcomment', interaction)
    self.logger.log_only('debug', f"arg : {héros_ou_pet} | commentaire : {commentaire}")
    await self.interaction_handler.handle_response(interaction=interaction, wait_msg=True)
    response = await self.get_response(héros_ou_pet, commentaire, nick(interaction), interaction)
    await self.interaction_handler.handle_response(interaction=interaction, response=response)
    self.logger.ok_log('addcomment')

  async def get_response(self, h_or_p, comment, author, interaction):
    if str_to_slug(h_or_p) == 'help':
      return self.help_msg
    if comment is not None:
      comment_result = await self.post_comment(h_or_p, comment, author, interaction)
      match comment_result['type']:
        case 'hero':
          hero_cog = Hero(self.bot)
          response = await hero_cog.get_response(comment_result['updated'].get('name'), interaction)
        case 'pet':
          pet_cog = Pet(self.bot)
          response = await pet_cog.get_response(comment_result['updated'].get('name'), interaction)
        case 'error':
          self.logger.log_only('debug', f"arg non trouvé dans la BDD : {h_or_p}")
          description = f"{self.error_msg['description']['addcomment'][0]['text']} {h_or_p} {self.error_msg['description']['addcomment'][1]['text']}"
          response = {'title': self.error_msg['title'], 'description': description, 'color': self.error_msg['color']}
      return response
    else:
      self.logger.log_only('debug', "commentaire vide")
      description = f"{self.error_msg['description']['addcomment'][2]['text']}"
      return {'title': self.error_msg['title'], 'description': description, 'color': self.error_msg['color']}

  async def post_comment(self, h_or_p, comment, author, interaction):
    comment = await self.bot.back_requests.call('addComment', False, [h_or_p, comment, author], interaction)
    if not comment:
      return {'type': 'error', 'updated': None}
    
    updated = await self.bot.back_requests.call('getHeroByName', False, [h_or_p], interaction)
    if updated:
      return {'type': 'hero', 'updated': updated}
    
    updated = await self.bot.back_requests.call('getPetByName', False, [h_or_p], interaction)
    if updated:
      return {"type": 'pet', "updated": updated}
  
  async def init_choices(self, param_list):
    if param_list is None:
      heroes = await self.bot.back_requests.call('getAllHeroes', False)
      if not heroes:
        return [{'name': 'Échec du chargement des héros'}]
    else:
      heroes = param_list[0]
    to_return = [{'name': h['name'], 'name_slug': h['name_slug']} for h in heroes]

    if param_list is None:
      pets = await self.bot.back_requests.call('getAllPets', False)
      if not pets:
        return to_return
    else:
      pets = param_list[1]  
    to_return.extend([{'name': p['name'], 'name_slug': p['name_slug']} for p in pets])
    
    return to_return
  
  async def setup(self, param_list):
    choices = await self.init_choices(param_list)
    self.choices = CommandService.set_choices(choices)
  
async def setup(bot):
  await bot.add_cog(Addcomment(bot))