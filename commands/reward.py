import typing
import discord
import emoji

from typing import Optional
from discord.app_commands import Choice

from discord.ext import commands
from discord import app_commands
from discord.ui import Button

from service.command import CommandService
from utils.sendMessage import SendMessage

class Reward(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.reward_command = next((c for c in bot.static_data.commands if c['name'] == 'reward'), None)
    self.gear_qualities = [g for g in bot.static_data.qualities if g['type'] == 'gear']
    self.dust_qualities = bot.static_data.dusts

    self.command_service = CommandService()
    CommandService.init_command(self.reward_app_command, self.reward_command)
    self.choices = None

  class ButtonData:
    def __init__(self, level_name: str, emojis, quantity: int, reward_type: str):
      self.level_name = level_name
      self.emojis = emojis
      self.reward_type = reward_type
      self.quantity = quantity

  class RewardButton(Button):
    def __init__(self, outer, button_data: 'Reward.ButtonData', icon: str, quality: Optional[str]=''):
      super().__init__(label=quality, emoji=icon)
      self.outer = outer
      self.quality = quality
      self.icon = icon
      self.level_name = button_data.level_name
      self.reward_type = button_data.reward_type
      self.button_data = button_data

    async def callback(self, interaction: discord.Interaction):
      try:
        response = await self.outer.bot.level_service.get_reward_response('add', self.button_data.emojis, self.level_name, self.reward_type, self.button_data.quantity, self.quality)
        await self.outer.send_message.update_remove_view(interaction, response)
      except Exception as e:
        self.outer.logger.error_log(f"Error in callback: {e}")
      self.outer.logger.ok_log('reward')

  class QualitySelectionView(discord.ui.View):
    def __init__(self, outer, button_data: 'Reward.ButtonData', qualities):
      super().__init__()
      qualities = sorted(qualities, key=lambda k: k['grade'])
      for quality in qualities:
        quality_name = quality.get('name')
        icon = emoji.emojize(quality.get('icon'))
        self.add_item(outer.RewardButton(outer, button_data, icon, quality_name))

  async def level_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await self.command_service.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(level=level_autocomplete)
  @app_commands.command(name='reward')
  async def reward_app_command(self, interaction: discord.Interaction, level: str, type: Choice[int], quantity: int):
    self.logger.command_log('reward', interaction)
    self.logger.log_only('debug', f"level : {level} | type : {type} | quantity : {quantity}")
    button_data = self.ButtonData(level, interaction.guild.emojis, quantity, type.name)

    if type.name == 'dust':
      view = self.QualitySelectionView(self, button_data, self.dust_qualities)
      await interaction.response.send_message(content="\n ## Choississez la qualité de la poussière ##", view=view)

    elif type.name == 'gear':
      view = self.QualitySelectionView(self, button_data, self.gear_qualities)
      await interaction.response.send_message(content="\n ##Choississez la qualité de l'objet ##", view=view)

    else:
      await self.send_message.post(interaction)
      response = await self.bot.level_service.get_reward_response('add', interaction.guild.emojis, level, type.name, quantity)
      await self.send_message.update(interaction, response)
      self.logger.ok_log('reward')

  async def setup(self):
    choices = await self.bot.back_requests.call('getAllLevels', False)
    self.choices = CommandService.set_choices([{'name': c.get('name')} for c in choices]) 

async def setup(bot):
  await bot.add_cog(Reward(bot))