import discord
from utils.message import Message
from utils.misc_utils import get_discord_color

class WaitMessage:
  def __init__(self, bot):
    self.bot = bot
    self.message = Message(bot)

  async def post(self, interaction):
    bot_msg = self.message.message('wait')
    initial_response = discord.Embed(title = bot_msg['title'], description = bot_msg['description'], color = get_discord_color(bot_msg['color']))
    await interaction.response.send_message(embed = initial_response)

  async def update(self, interaction, new_message):
    bot_response = discord.Embed(title=new_message['title'], description = new_message['description'], color = get_discord_color(new_message['color']))
    if new_message['pic'] is not None:
      bot_response.set_thumbnail(url = new_message['pic'])
    await interaction.edit_original_response(embed = bot_response)