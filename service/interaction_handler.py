import discord
import asyncio
from discord.errors import HTTPException, InteractionResponded

from utils.message import Message
from utils.misc_utils import get_discord_color, convert_seconds

max_attempts = 3

class InteractionHandler:
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.message = Message(bot)
    self.error_message = Message(bot).message('error')
    self.original_message_id = None
    self.was_a_modal = False
    self.last_content = None

  async def handle_response(self, interaction: discord.Interaction, response=None, content='', view=None, modal=None, wait_msg=False, more_response='', generic_error_msg=False, timeout=None):
    self.logger.log_only('debug', f'interactionId: {interaction.id}')
    for attempt in range(max_attempts):
      try:
        if modal is not None:
          self.logger.log_only('debug', 'modal')
          if hasattr(interaction, 'message') and interaction.message:
            self.original_message_id = interaction.message.id
          self.was_a_modal = True
          return await interaction.response.send_modal(modal)

        if not interaction.response.is_done():
          await interaction.response.defer()

        if view is not None and response is None:
          self.logger.log_only('debug', 'view only')
          return await self.handle_view_response(interaction, content, view)
        
        if response is not None and view is None:
          self.logger.log_only('debug', 'embed only')
          embed = self.build_embed(response, wait_msg, more_response, generic_error_msg, timeout)
          return await self.handle_embed_response(interaction, embed)
        
        self.logger.log_only('debug', 'view & embed')
        embed = self.build_embed(response, wait_msg, more_response, generic_error_msg, timeout)
        return await self.handle_view_and_embed_response(interaction, embed, view)

      except (HTTPException, InteractionResponded) as e:
        if attempt == max_attempts - 1:
          self.logger.log_only('warning', f'Échec de l\'interaction après {max_attempts} tentatives : {e}')
        await asyncio.sleep(1)

      except Exception as e:
        self.logger.log_only('warning', f'Erreur d\'interaction non gérée : {e}')

  async def handle_view_response(self, interaction: discord.Interaction, content, view):
    if content == '':
      content = self.last_content

    if self.original_message_id and hasattr(interaction, 'message'):
      try:
        original_message = await interaction.channel.fetch_message(self.original_message_id)
        self.logger.log_only('debug', 'view after modal with an original message')
        new_message = await original_message.edit(content=content, embed=None, view=view)
        self.last_content = content
        self.original_message_id = None
        self.was_a_modal = False
        return new_message
      except Exception as e:
        self.logger.log_only('debug', f'erreur : {e}')

    if self.was_a_modal:
      try:
        self.logger.log_only('debug', 'view after modal with no original message')
        self.was_a_modal = False
        return await interaction.followup.send(content=content, embed=None, view=view)        
      except Exception as e:
        self.logger.log_only('debug', f'erreur : {e}')

    try:
      self.last_content = content
      return await interaction.edit_original_response(content=content, embed=None, view=view)
    except Exception as e:
      self.logger.log_only('debug', f'erreur : {e}')
      try:
        self.last_content = content
        return await interaction.response.edit_message(content=content, embed=None, view=view)
      except Exception as e:
        self.logger.log_only('debug', f'erreur : {e}')
        self.last_content = content
        return await interaction.response.send_message(content=content, embed=None, view=view)
    
    
  async def handle_embed_response(self, interaction: discord.Interaction, embed):
    if self.original_message_id and hasattr(interaction, 'message'):
      try:
        original_message = await interaction.channel.fetch_message(self.original_message_id)
        self.logger.log_only('debug', 'embed after modal with an original message')
        new_message = await original_message.edit(content='', embed=embed, view=None)
        self.original_message_id = None
        self.was_a_modal = False
        return new_message
      except Exception as e:
        self.logger.log_only('debug', f'erreur : {e}')

    if self.was_a_modal:
      try:
        self.logger.log_only('debug', 'embed after modal with no original message')
        self.was_a_modal = False
        return await interaction.followup.send(content='', embed=embed, view=None)        
      except Exception as e:
        self.logger.log_only('debug', f'erreur : {e}')

    try:
      return await interaction.edit_original_response(content='', embed=embed, view=None)
    except Exception as e:
      self.logger.log_only('debug', f'erreur : {e}')
      try:
        return await interaction.response.edit_message(content='', embed=embed, view=None)
      except Exception as e:
        self.logger.log_only('debug', f'erreur : {e}')
        return await interaction.response.send_message(content='', embed=embed, view=None)
  
  async def handle_view_and_embed_response(self, interaction: discord.Interaction, embed, view):
    if self.original_message_id and hasattr(interaction, 'message'):
      try:
        original_message = await interaction.channel.fetch_message(self.original_message_id)
        self.logger.log_only('debug', 'embed&view after modal with an original message')
        new_message = await original_message.edit(content='', embed=embed, view=view)
        self.original_message_id = None
        self.was_a_modal = False
        return new_message
      except Exception as e:
        self.logger.log_only('debug', f'erreur : {e}')

    if self.was_a_modal:
      try:
        self.logger.log_only('debug', 'embed&view after modal with no original message')
        self.was_a_modal = False
        return await interaction.followup.send(content='', embed=embed, view=view)
      except Exception as e:
        self.logger.log_only('debug', f'erreur : {e}')

    try:
      return await interaction.edit_original_response(content='', embed=embed, view=view)
    except Exception as e:
      self.logger.log_only('debug', f'erreur : {e}')
      try:
        return await interaction.response.edit_message(content='', embed=embed, view=view)
      except Exception as e:
        self.logger.log_only('debug', f'erreur : {e}')
        return await interaction.response.send_message(content='', embed=embed, view=view)

  def build_embed(self, response, wait_msg, more_response, generic_error_msg, timeout):
    if response is None and not wait_msg and not generic_error_msg and not timeout:
      return None

    if response is not None:
      footer_msg = self.message.message('footer')

      if len(response.get('description')) + len(footer_msg.get('ok')) > 4096:
        taille_max = 4096 - len(footer_msg.get('ok')) - len(footer_msg.get('too_long'))
        response['description'] = response.get('description')[0:taille_max] + footer_msg.get('too_long')
      embed = discord.Embed(title=response.get('title'), description=response.get('description'), color=get_discord_color(response.get('color')))

      if 'image' in response.keys():
        embed.set_image(url=response.get('image'))
      if 'thumbnail' in response.keys():
        embed.set_thumbnail(url=response.get('thumbnail'))

      embed.set_footer(text=footer_msg.get('ok'))
    elif wait_msg:
      tempo_response = self.message.message('wait')
      embed = discord.Embed(title = tempo_response.get('title'), description = tempo_response.get('description') + more_response, color=get_discord_color(tempo_response.get('color')))
    elif generic_error_msg:
      error_response = self.error_message.get('description').get('generic')[0].get('text')
      embed = discord.Embed(title = self.error_message.get('title'), description = error_response, color=get_discord_color(self.error_message.get('color')))
    elif timeout is not None:
      inactivity_time = convert_seconds(timeout)
      embed = discord.Embed(title='Session expirée ⏰', description=f'La commande a été annulée après {inactivity_time} :shrug:\nMerci de réitérer la commande :wink:', color=get_discord_color('red'))
      self.logger.log_only('debug', 'command timeout')
    else:
      self.logger.log_only('warning', 'foirage de paramètres :)')
      return None
    return embed