import typing
import requests

import discord
from discord.ext import commands
from discord import app_commands

from service.command import CommandService
from utils.sendMessage import SendMessage

from utils.logger import Logger
from config import DB_PATH

class Level(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.level_data = bot.level_data
    self.level_command = next((c for c in bot.static_data.commands if c['name'] == 'level'), None)

    CommandService.init_command(self.level_app_command, self.level_command)


  async def level_autocompletion(self, interaction: discord.Interaction, current: str
                                 ) -> typing.List[app_commands.Choice[str]]:
    return [level for level in self.level_data.known_levels if current in level.name][:25]

  @app_commands.command(name='level')
  async def level_app_command(self, interaction: discord.Interaction, name: str, cost: int):
    Logger.command_log('level', interaction)
    author = str(interaction.user)
    if "spirou" not in author and "prep" not in author:
      await self.send_message.error(interaction, "Cette commande n'est pas publique pour l'instant", "Veuillez contacter Prep ou Spirou pour ajouter votre niveau à la liste.")
      Logger.ok_log('level')
      return

    await self.send_message.post(interaction)
    response = self.get_level_response(name, cost)
    await self.send_message.update(interaction, response)
    self.level_data.load_levels()
    Logger.ok_log('level')

  def get_level_response(self, level_name, level_cost):
    if level_name in [known_level.name for known_level in self.level_data.known_levels]:
      return {'title': f'Le niveau {level_name} existe déjà', 'description': "Tout est prêt pour l'utilisation des commandes reward et reward-stat",
              'color': 'blue'}
    level = self.create_level(level_name, level_cost)

    return {'title': f'Le niveau {level.get('name')} a été ajouté', 'description': "Merci d'avoir ajouté ce niveau!",
            'color': 'blue'}

  def create_level(self, name, cost):
    data = {
      "name": name,
      "cost": cost
    }
    return requests.post(f"{DB_PATH}levels", json=data).json()

async def setup(bot):
  await bot.add_cog(Level(bot))