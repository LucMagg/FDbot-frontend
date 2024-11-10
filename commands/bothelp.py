import discord
from discord.ext import commands
from discord import app_commands

from service.command import CommandService
from utils.sendMessage import SendMessage
from utils.message import Message


class Bothelp(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'bothelp'), None)
    self.help_msg = Message(bot).help('help')

    CommandService.init_command(self.bothelp_app_command, self.command)

  @app_commands.command(name='bothelp')
  async def bothelp_app_command(self, interaction: discord.Interaction):
    self.logger.command_log('bothelp', interaction)
    await self.send_message.handle_response(interaction=interaction, wait_msg=True)
    await self.send_message.handle_response(interaction=interaction, response=self.help_msg)
    self.logger.ok_log('bothelp')

  
async def setup(bot):
  await bot.add_cog(Bothelp(bot))