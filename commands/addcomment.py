import discord
from discord.ext import commands
from discord import app_commands
import requests
from typing import Optional

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

    if self.command:
      self.addcomment_app_command.name = self.command['name']
      self.addcomment_app_command.description = self.command['description']
      self.addcomment_app_command._params['héros_ou_pet'].description = self.command['options'][0]['description']
      self.addcomment_app_command._params['commentaire'].description = self.command['options'][1]['description']
      self.addcomment_app_command._params['commentaire'].required = False


  @app_commands.command(name='addcomment')
  async def addcomment_app_command(self, interaction: discord.Interaction, héros_ou_pet: str, commentaire: Optional[str] = None):
    Logger.command_log('addcomment', interaction)
    await self.send_message.post(interaction)
    response = Addcomment.get_response(self, héros_ou_pet, commentaire, nick(interaction))
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
    comment = requests.post(f"{DB_PATH}comment?hero_or_pet={str_to_slug(h_or_p)}&comment={comment}&author={author}").json()
    if 'error' not in comment.keys():
      print('here')
      updated = requests.get(f"{DB_PATH}hero/{str_to_slug(h_or_p)}").json()
      type = 'hero'
      if 'error'in updated.keys():
        updated = requests.get(f"{DB_PATH}pet/{str_to_slug(h_or_p)}").json()
        type = 'pet'
    else:
      updated = comment
      type = 'error'
    return {"type": type, "updated": updated}
  
async def setup(bot):
  await bot.add_cog(Addcomment(bot))