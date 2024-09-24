import typing
from typing import Optional

from statistics import quantiles
import requests

import discord
from discord.app_commands import Choice
from discord.ext import commands
from discord import app_commands
from discord.ui import Button
import emoji

from service.command import CommandService
from utils.sendMessage import SendMessage

from utils.logger import Logger
from utils.misc_utils import pluriel
from config import DB_PATH

class Level(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.known_levels = self.get_known_levels()
    self.level_command = next((c for c in bot.static_data.commands if c['name'] == 'level'), None)
    self.reward_command = next((c for c in bot.static_data.commands if c['name'] == 'reward'), None)
    self.reward_stat_command = next((c for c in bot.static_data.commands if c['name'] == 'reward-stat'), None)
    self.gear_qualities = [g for g in bot.static_data.qualities if g['type'] == 'gear']
    self.dust_qualities = bot.static_data.dusts

    CommandService.init_command(self.level_app_command, self.level_command)
    CommandService.init_command(self.reward_app_command, self.reward_command)
    CommandService.init_command(self.reward_stat_app_command, self.reward_stat_command)


  async def level_autocompletion(self, interaction: discord.Interaction, current: str
                                 ) -> typing.List[app_commands.Choice[str]]:
    return [level for level in self.known_levels if current in level.name]

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
    self.known_levels = self.get_known_levels()
    Logger.ok_log('level')

  def get_level_response(self, level_name, level_cost):
    if level_name in [known_level.name for known_level in self.known_levels]:
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

  def add_reward(self, level_name, reward_type, reward_quantity, reward_quality: Optional[str]= ''):
    data = {
      "type": reward_type,
      "quantity": reward_quantity,
      "quality": reward_quality
    }
    return requests.post(f"{DB_PATH}levels/{level_name}/reward", json=data).json()

  def get_levels():
    return requests.get(f"{DB_PATH}levels").json()

  def get_level(level_name):
    return requests.get(f"{DB_PATH}levels/{level_name}").json()

  def get_potion_emoji(self, guild):
        potion_emoji = discord.utils.get(guild.emojis, name='potion')
        print(str(potion_emoji))
        return str(potion_emoji) if potion_emoji else ''

  def get_rewards_str(self, rewards, guild):
    total_reward_appearances = sum([reward.get('appearances') for reward in rewards])
    quantities = []
    for r in rewards:
      match r.get('type'):
        case 'gold':
          icon = ':moneybag:'
        case 'gear':
          icon = next((g.get('icon') for g in self.gear_qualities if g.get('name') == r.get('quality')), None)
        case 'dust':
          icon = next((d.get('icon') for d in self.dust_qualities if d.get('name') == r.get('quality')), None)
        case 'potions':
          icon = self.get_potion_emoji(guild)
  

      quantities.append(f"{icon} {r.get('quantity')} {r.get('quality', '')} {r.get('type')}: {format(r.get('appearances') / total_reward_appearances, '.2%')} ({r.get('appearances')})\n")
    return f'{total_reward_appearances} récompense{pluriel(total_reward_appearances)} recueillie{pluriel(total_reward_appearances)}:\n' + '\n'.join([q for q in quantities])

  @app_commands.autocomplete(level=level_autocompletion)
  @app_commands.command(name='reward')
  async def reward_app_command(self, interaction: discord.Interaction, level: str, type: Choice[int], quantity: int):
    Logger.command_log('reward', interaction)
    if type.name == 'dust':
      await interaction.response.send_message(content="Choississez la qualité de la poussière",
                                              view=RewardQualitySelectionView(interaction.guild, self.send_message, self.dust_qualities, self, level, quantity, type.name))
    elif type.name == 'gear':
      await interaction.response.send_message(content="Choississez la qualité de l'objet",
                                              view=RewardQualitySelectionView(interaction.guild, self.send_message, self.gear_qualities, self, level, quantity, type.name))
    else:
      await self.send_message.post(interaction)
      response = self.get_reward_response(interaction.guild, level, type.name, quantity)
      await self.send_message.update(interaction, response)
      Logger.ok_log('reward')

  @app_commands.autocomplete(level=level_autocompletion)
  @app_commands.command(name='reward-stat')
  async def reward_stat_app_command(self, interaction: discord.Interaction, level: str):
    Logger.command_log('reward-stat', interaction)
    if level not in [level.name for level in self.known_levels]:
      await self.send_message.error(interaction, "Ce niveau n'existe pas", "Veuillez choisir un niveau dans la liste ou contacter Prep ou Spirou.")
      Logger.ok_log('reward')
      return

    await self.send_message.post(interaction)
    response = self.get_reward_stat_response(level, interaction.guild)
    await self.send_message.update(interaction, response)
    Logger.ok_log('reward')

  def get_reward_response(self, guild, level_name, reward_type, reward_quantity, reward_quality: Optional[str] = ''):
    level = Level.add_reward(self, level_name, reward_type, reward_quantity, reward_quality)
    quantities_str = Level.get_rewards_str(self, level.get('rewards', []), guild)

    return {'title': f'Récompense ajoutée au niveau {level.get('name')}', 'description': f"Merci d'avoir ajouté une récompense à ce niveau! \nStatistiques actuelles pour ce niveau:\n{quantities_str}",
            'color': 'blue'}

  def get_reward_stat_response(self, level_name, guild):
    level = Level.get_level(level_name)
    quantities_str = Level.get_rewards_str(self, level.get('rewards', []), guild)

    return {'title': f'Statistiques pour le niveau {level.get('name')}', 'description': f'Statistiques actuelles pour ce niveau:\n{quantities_str}',
            'color': 'blue'}

  def get_known_levels(self):
    levels = Level.get_levels()
    levels_choices = [Choice(name=l.get('name'), value=l.get('name')) for l in levels]

    return levels_choices
  
class TypeButton(Button):
  def __init__(self, guild, send_message, level_service: Level, level: str, quantity: int, icon: str, quality: str, reward_type: str):
    super().__init__(label=quality, emoji=icon)
    self.guild = guild
    self.quantity = quantity
    self.quality = quality
    self.icon = icon
    self.level_name = level
    self.reward_type = reward_type
    self.send_message = send_message
    self.level_service = level_service

  async def callback(self, interaction: discord.Interaction):
    try:
      response = self.level_service.get_reward_response(self.guild, self.level_name, self.reward_type, self.quantity, self.quality)
      await self.send_message.update_remove_view(interaction, response)
    except Exception as e:
      print(f"Error in callback: {e}")
    Logger.ok_log('reward')

class RewardQualitySelectionView(discord.ui.View):
  def __init__(self, guild, send_message, qualities, level_service: Level, level: str, quantity: int, type: str):
    super().__init__()
    qualities = sorted(qualities, key=lambda k: k['grade'])
    for quality in qualities:
      name = quality.get('name')
      icon = emoji.emojize(quality.get('icon'))
      self.add_item(TypeButton(guild, send_message, level_service, level, quantity, icon, name, type))
  
async def setup(bot):
  await bot.add_cog(Level(bot))