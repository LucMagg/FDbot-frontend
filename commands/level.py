import typing
import requests

import discord
from discord.ext import commands
from discord import app_commands

from service.command import CommandService
from utils.sendMessage import SendMessage

from config import DB_PATH

class Level(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.level_command = next((c for c in bot.static_data.commands if c['name'] == 'level'), None)

    self.command_service = CommandService()
    CommandService.init_command(self.level_app_command, self.level_command)
    self.choices = None


  async def level_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await self.command_service.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(name=level_autocomplete)
  @app_commands.command(name='level')
  async def level_app_command(self, interaction: discord.Interaction, name: str, cost: int):
    self.logger.command_log('level', interaction)
    self.logger.log_only('debug', f"name : {name} | cost : {cost}")
    author = str(interaction.user)
    if "spirou" not in author and "prep" not in author:
      await self.send_message.error(interaction, "Cette commande n'est pas publique pour l'instant", "Veuillez contacter Prep ou Spirou pour ajouter votre niveau à la liste.")
      self.logger.log_only('debug', f"user {author} non autorisé")
      self.logger.ok_log('level')
      return

    await self.send_message.post(interaction)
    response = await self.get_level_response(name, cost)
    await self.send_message.update(interaction, response)
    await self.commands_to_update(['level', 'reward', 'rewardstat'])
    self.logger.ok_log('level')

  async def get_level_response(self, level_name, level_cost):
    if level_name in [c.name for c in self.choices]:
      self.logger.log_only('debug', f"level déjà existant")
      return {'title': '', 'description': f"# Le niveau {level_name} existe déjà #\nTout est prêt pour l'utilisation des commandes reward et reward-stat :wink:", 'color': 'blue'}
    level = await self.create_level(level_name, level_cost)
    return {'title': '', 'description': f"# Le niveau {level.get('name')} a été ajouté#\nMerci d'avoir ajouté ce niveau ! :kissing_heart:", 'color': 'blue'}

  async def create_level(self, name, cost):
    data = {
      "name": name,
      "cost": cost
    }
    return await self.bot.back_requests.call('addLevel', False, [data])
  
  async def commands_to_update(self, command_list):
    levels = await self.bot.back_requests.call('getAllLevels', False)
    for command in command_list:
      command_location = f"commands.{command}"
      if levels:
        await self.bot.setup_command(command_location, levels)
      else:
        await self.bot.setup_command(command_location)
      
  async def setup(self, param_list):
    if param_list is None:
      choices = await self.bot.back_requests.call('getAllLevels', False)
    else:
      choices = param_list
    self.choices = CommandService.set_choices([{'name': c.get('name')} for c in choices]) 

async def setup(bot):
  await bot.add_cog(Level(bot))