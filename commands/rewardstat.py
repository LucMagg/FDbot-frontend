import typing
import discord

from discord.ext import commands
from discord import app_commands

from service.command import CommandService
from utils.sendMessage import SendMessage

class Rewardstat(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.reward_stat_command = next((c for c in bot.static_data.commands if c['name'] == 'rewardstat'), None)

    self.command_service = CommandService()
    CommandService.init_command(self.reward_stat_app_command, self.reward_stat_command)
    self.choices = None

  async def level_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await self.command_service.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(level=level_autocomplete)
  @app_commands.command(name='rewardstat')
  async def reward_stat_app_command(self, interaction: discord.Interaction, level: str):
    self.logger.command_log('rewardstat', interaction)
    self.logger.log_only('debug', f"level : {level}")
    if level not in [c.name for c in self.choices]:
      self.logger.log_only('debug', f"level inexistant")
      await self.send_message.error(interaction, "Ce niveau n'existe pas", "Veuillez choisir un niveau dans la liste ou contacter Prep ou Spirou.")
      self.logger.ok_log('rewardstat')
      return

    await self.send_message.post(interaction)
    response = await self.bot.level_service.display_rewards(interaction.guild.emojis, level)
    await self.send_message.update(interaction, response)
    self.logger.ok_log('rewardstat')

  async def setup(self, param_list):
    if param_list is None:
      choices = await self.bot.back_requests.call('getAllLevels', False)
    else:
      choices = param_list
    self.choices = CommandService.set_choices([{'name': c.get('name')} for c in choices]) 

async def setup(bot):
  await bot.add_cog(Rewardstat(bot))