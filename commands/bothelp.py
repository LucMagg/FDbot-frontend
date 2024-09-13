import discord
from discord.ext import commands
from discord import app_commands

from utils.sendMessage import SendMessage
from utils.message import Message
from utils.logger import Logger

class Bothelp(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'bothelp'), None)
    self.help_msg = Message(bot).help('help')

    if self.command:
      self.bothelp_app_command.name = self.command['name']
      self.bothelp_app_command.description = self.command['description']


  @app_commands.command(name='bothelp')
  async def bothelp_app_command(self, interaction: discord.Interaction):
    Logger.command_log('bothelp', interaction)
    await self.send_message.post(interaction)
    response = self.help_msg
    await self.send_message.update(interaction, response)
    Logger.ok_log('bothelp')

  
async def setup(bot):
  await bot.add_cog(Bothelp(bot))