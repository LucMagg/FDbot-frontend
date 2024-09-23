import discord
from discord import Color
from utils.message import Message
from utils.misc_utils import get_discord_color

class SendMessage:
  def __init__(self, bot):
    self.bot = bot
    self.message = Message(bot)

  async def post(self, interaction, more_msg = ''):
    bot_msg = self.message.message('wait')
    initial_response = discord.Embed(title = bot_msg['title'], description = bot_msg['description'] + more_msg, color = get_discord_color(bot_msg['color']))
    await interaction.response.send_message(embed = initial_response)


  async def update(self, interaction, new_message):
    footer_msg = self.message.message('footer')
    if len(new_message['description']) + len(footer_msg['ok']) > 4096:
      taille_max = 4096 - len(footer_msg['ok']) - len(footer_msg['too_long'])
      new_message['description'] = new_message['description'][0:taille_max] + footer_msg['too_long']

    bot_response = discord.Embed(title=new_message['title'], description=new_message['description'],
                                 color=get_discord_color(new_message['color']))

    if 'image' in new_message.keys():
      bot_response.set_image(url=new_message['image'])
    elif 'pic' in new_message.keys():
      if new_message['pic'] is not None:
        bot_response.set_thumbnail(url=new_message['pic'])
    bot_response.set_footer(text=footer_msg['ok'])

    await interaction.edit_original_response(embed=bot_response)

  async def update_remove_view(self, interaction, new_message):
    footer_msg = self.message.message('footer')
    if len(new_message['description']) + len(footer_msg['ok']) > 4096:
      taille_max = 4096 - len(footer_msg['ok']) - len(footer_msg['too_long'])
      new_message['description'] = new_message['description'][0:taille_max] + footer_msg['too_long']

    bot_response = discord.Embed(title=new_message['title'], description=new_message['description'],
                                 color=get_discord_color(new_message['color']))

    if 'image' in new_message.keys():
      bot_response.set_image(url=new_message['image'])
    elif 'pic' in new_message.keys():
      if new_message['pic'] is not None:
        bot_response.set_thumbnail(url=new_message['pic'])
    bot_response.set_footer(text=footer_msg['ok'])

    await interaction.response.edit_message(embed=bot_response, view=None, content=None)

  async def error(self, interaction, title, description):
    initial_response = discord.Embed(title=title, description=description, color=Color.from_rgb(255, 0, 0))
    await interaction.response.send_message(embed=initial_response)
