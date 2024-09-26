import typing
import discord
import emoji
import requests

from typing import Optional
from discord.app_commands import Choice

from discord.ext import commands
from discord import app_commands
from discord.ui import Button

from config import DB_PATH
from service.command import CommandService
from service.level import LevelService
from utils.logger import Logger
from utils.misc_utils import pluriel
from utils.sendMessage import SendMessage

class Reward(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.level_data = bot.level_data
    self.reward_command = next((c for c in bot.static_data.commands if c['name'] == 'reward'), None)
    self.gear_qualities = [g for g in bot.static_data.qualities if g['type'] == 'gear']
    self.dust_qualities = bot.static_data.dusts

    CommandService.init_command(self.reward_app_command, self.reward_command)

  async def level_autocompletion(self, interaction: discord.Interaction, current: str
                                 ) -> typing.List[app_commands.Choice[str]]:
    return [level for level in self.level_data.known_levels if current in level.name][:25]


  @app_commands.autocomplete(level=level_autocompletion)
  @app_commands.command(name='reward')
  async def reward_app_command(self, interaction: discord.Interaction, level: str, type: Choice[int], quantity: int):
    Logger.command_log('reward', interaction)
    reward_button_data = RewardButtonData(level, interaction.guild.emojis, self.gear_qualities, self.dust_qualities, quantity, type.name)

    if type.name == 'dust':
      view = RewardQualitySelectionView(self.send_message, reward_button_data, self.dust_qualities)
      await interaction.response.send_message(content="Choississez la qualité de la poussière", view=view)
    elif type.name == 'gear':
      view = RewardQualitySelectionView(self.send_message, reward_button_data, self.gear_qualities)
      await interaction.response.send_message(content="Choississez la qualité de l'objet", view=view)
    else:
      await self.send_message.post(interaction)
      response = LevelService.get_reward_response('add', interaction.guild.emojis, level, type.name, quantity, self.gear_qualities, self.dust_qualities)
      await self.send_message.update(interaction, response)
      Logger.ok_log('reward')


class RewardButtonData:
  def __init__(self, level_name: str, emojis, gear_qualities, dust_qualities, quantity: int, reward_type: str):
    self.level_name = level_name
    self.emojis = emojis
    self.gear_qualities = gear_qualities
    self.dust_qualities = dust_qualities
    self.reward_type = reward_type
    self.quantity = quantity

class RewardButton(Button):
  def __init__(self, send_message, reward_button_data: RewardButtonData, icon: str, quality: Optional[str]=''):
    super().__init__(label=quality, emoji=icon)
    self.quality = quality
    self.icon = icon
    self.level_name = reward_button_data.level_name
    self.reward_type = reward_button_data.reward_type
    self.reward_button_data = reward_button_data
    self.send_message = send_message

  async def callback(self, interaction: discord.Interaction):
    try:
      response = LevelService.get_reward_response('add', self.reward_button_data.emojis, self.level_name, self.reward_type, self.reward_button_data.quantity,
                                                  self.reward_button_data.gear_qualities, self.reward_button_data.dust_qualities, self.quality)
      await self.send_message.update_remove_view(interaction, response)
    except Exception as e:
      print(f"Error in callback: {e}")
    Logger.ok_log('reward')

class RewardQualitySelectionView(discord.ui.View):
  def __init__(self, send_message, reward_button_data: RewardButtonData, qualities):
    super().__init__()
    qualities = sorted(qualities, key=lambda k: k['grade'])
    for quality in qualities:
      quality_name = quality.get('name')
      icon = emoji.emojize(quality.get('icon'))
      self.add_item(RewardButton(send_message, reward_button_data, icon, quality_name))

async def setup(bot):
  await bot.add_cog(Reward(bot))