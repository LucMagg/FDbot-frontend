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

    CommandService.init_command(self.reward_stat_app_command, self.reward_stat_command)
    self.choices = None

  async def level_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await CommandService.return_autocompletion(self.choices, current)

  @app_commands.autocomplete(level=level_autocomplete)
  @app_commands.command(name='rewardstat')
  async def reward_stat_app_command(self, interaction: discord.Interaction, level: str):
    self.logger.command_log('rewardstat', interaction)
    self.logger.log_only('debug', f"level : {level}")
    await self.send_message.handle_response(interaction=interaction, wait_msg=True)

    if level not in [c.name for c in self.choices]:
      self.logger.log_only('debug', f"level inexistant")
      response = {'title': 'Erreur !', 'description': 'Ce niveau n\'existe pas.\nVeuillez choisir un niveau dans la liste ou contacter Prep ou Spirou.', 'color': 'red'}
      await self.send_message.handle_response(interaction=interaction, response=response)
      self.logger.ok_log('rewardstat')
      return

    response = await self.bot.level_service.display_rewards(interaction.guild.emojis, level)
    await self.send_message.handle_response(interaction, response)
    self.logger.ok_log('rewardstat')

  async def setup(self, param_list):
    if param_list is None:
      choices = await self.bot.back_requests.call('getAllLevels', False)
    else:
      choices = param_list
    self.choices = CommandService.set_choices_by_rewards(choices) 

async def setup(bot):
  await bot.add_cog(Rewardstat(bot))