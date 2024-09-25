import discord
from discord.ext import commands
from discord import app_commands
import requests
import typing
from typing import Optional

from service.command import CommandService
from utils.message import Message
from utils.sendMessage import SendMessage
from utils.str_utils import str_to_slug
from utils.misc_utils import nick
from utils.logger import Logger
from config import DB_PATH

from commands.hero import Hero
from commands.pet import Pet


class Addcomment(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'addcomment'), None)
    self.error_msg = Message(bot).message('error')
    self.help_msg = Message(bot).help('addcomment')

    self.command_service = CommandService()
    CommandService.init_command(self.addcomment_app_command, self.command)
    self.choices = CommandService.set_choices(Addcomment.merged_lists())

  async def héros_ou_pet_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await self.command_service.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(héros_ou_pet=héros_ou_pet_autocomplete)
  @app_commands.command(name='addcomment')
  async def addcomment_app_command(self, interaction: discord.Interaction, héros_ou_pet: str, commentaire: Optional[str] = None):
    Logger.command_log('addcomment', interaction)
    await self.send_message.post(interaction)
    response = self.get_response(héros_ou_pet, commentaire, nick(interaction))
    await self.send_message.update(interaction, response)
    Logger.ok_log('addcomment')

  def get_response(self, h_or_p, comment, author):
    if str_to_slug(h_or_p) == 'help':
      return self.help_msg
    if comment is not None:
      comment = Addcomment.post_comment(h_or_p, comment, author)
      match comment['type']:
        case 'hero':
          response = Hero.get_response(self, comment['updated']['name'])
        case 'pet':
          response = Pet.get_response(self, comment['updated']['name'])
        case 'error':
          description = f"{self.error_msg['description']['addcomment'][0]['text']} {h_or_p} {self.error_msg['description']['addcomment'][1]['text']}"
          response = {'title': self.error_msg['title'], 'description': description, 'color': self.error_msg['color']}
      return response
    else:
      description = f"{self.error_msg['description']['addcomment'][2]['text']}"
      response = {'title': self.error_msg['title'], 'description': description, 'color': self.error_msg['color']}
      return response

  def post_comment(h_or_p, comment, author):
    comment = requests.post(f"{DB_PATH}comment?hero_or_pet={h_or_p}&comment={comment}&author={author}").json()
    if 'error' not in comment.keys():
      updated = requests.get(f"{DB_PATH}hero/{h_or_p}").json()
      type = 'hero'
      if 'error'in updated.keys():
        updated = requests.get(f"{DB_PATH}pet/{h_or_p}").json()
        type = 'pet'
    else:
      updated = comment
      type = 'error'
    return {"type": type, "updated": updated}
  
  def merged_lists():
    heroes = Addcomment.get_heroes()
    to_return = [{'name': h['name'], 'name_slug': h['name_slug']} for h in heroes]
    pets = Addcomment.get_pets()
    to_return.extend([{'name': p['name'], 'name_slug': p['name_slug']} for p in pets])
    return to_return
  
  def get_heroes():
    heroes = requests.get(f'{DB_PATH}hero').json()
    return heroes
  
  def get_pets():
    pets = requests.get(f'{DB_PATH}pet').json()
    return pets
  
async def setup(bot):
  await bot.add_cog(Addcomment(bot))