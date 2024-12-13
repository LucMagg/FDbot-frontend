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
    self.original_message_id = None
    self.was_a_modal = False
    self.last_content = None

  async def send_wait_message(self, interaction: discord.Interaction, more_response=''):
    wait_message = self.message.message('wait')
    embed = discord.Embed(
      title=wait_message.get('title'), 
      description=wait_message.get('description') + more_response,
      color=get_discord_color(wait_message.get('color')))
    self.logger.log_only('debug', 'send waiting message')
    return await self.handle_response(interaction=interaction, embed=embed)
  
  async def send_generic_error_message(self, interaction: discord.Interaction):
    error_message = self.message.message('error')
    embed = discord.Embed(
      title=error_message.get('title'),
      description=error_message.get('description').get('generic')[0].get('text'),
      color=get_discord_color(error_message.get('color')))
    self.logger.log_only('debug', 'send generic error message')
    return await self.handle_response(interaction=interaction, embed=embed)
  
  async def send_timeout_message(self, interaction: discord.Interaction, timeout: int):
    inactivity_time = convert_seconds(timeout)
    embed = discord.Embed(
      title='Session expirée ⏰',
      description=f'La commande a été annulée après {inactivity_time} :shrug:\nMerci de réitérer la commande :wink:',
      color=get_discord_color('red'))
    self.logger.log_only('debug', 'send command timeout')
    return await self.handle_response(interaction=interaction, embed=embed)
  
  async def send_embed(self, interaction: discord.Interaction, response: dict):
    embed = self.build_embed(response)
    self.logger.log_only('debug', 'send embed')
    return await self.handle_response(interaction=interaction, embed=embed)
  
  async def send_modal(self, interaction: discord.Interaction, modal: discord.ui.Modal):
    self.logger.log_only('debug', 'send modal')
    return await self.handle_response(interaction=interaction, modal=modal)
  
  async def send_view(self, interaction: discord.Interaction, view: discord.ui.View, content: str = ''):
    if content == '':
      content = self.last_content
    self.logger.log_only('debug', 'send view')
    return await self.handle_response(interaction=interaction, view=view, content=content)
  
  async def send_view_and_embed(self, interaction: discord.Interaction, response: dict, view: discord.ui.View):
    embed = self.build_embed(response)
    self.logger.log_only('debug', 'send view & embed')
    return await self.handle_response(interaction=interaction, embed=embed, view=view)

  def build_embed(self, response: dict):
    footer_msg = self.message.message('footer')
    if len(response.get('description')) + len(footer_msg.get('ok')) > 4096:
      taille_max = 4096 - len(footer_msg.get('ok')) - len(footer_msg.get('too_long'))
      response['description'] = response.get('description')[0:taille_max] + footer_msg.get('too_long')
    
    embed = discord.Embed(
      title=response.get('title'),
      description=response.get('description'),
      color=get_discord_color(response.get('color')))

    if 'image' in response.keys():
      embed.set_image(url=response.get('image'))
    if 'thumbnail' in response.keys():
      embed.set_thumbnail(url=response.get('thumbnail'))
    self.logger.log_only('debug', 'embed built')
    return embed
  
  async def handle_response(self, interaction: discord.Interaction, embed: discord.Embed = None, content: str = '', view: discord.ui.View = None, modal: discord.ui.Modal = None):
    self.logger.log_only('debug', f'interactionId: {interaction.id}')
    if embed is not None:
      embed.set_footer(text=self.message.message('footer').get('ok'))

    for attempt in range(max_attempts):
      try:
        if modal is not None:
          if hasattr(interaction, 'message') and interaction.message:
            self.original_message_id = interaction.message.id
          self.was_a_modal = True
          return await interaction.response.send_modal(modal)
        if not interaction.response.is_done():
          await interaction.response.defer()
        if view is not None and embed is None:
          return await self.handle_view_response(interaction=interaction, content=content, view=view)
        if view is None and embed is None:
          return await self.handle_embed_response(interaction=interaction, embed=embed)
        return await self.handle_view_and_embed_response(interaction=interaction, view=view, embed=embed)

      except (HTTPException, InteractionResponded) as e:
        if attempt == max_attempts - 1:
          self.logger.log_only('warning', f'Échec de l\'interaction après {max_attempts} tentatives : {e}')
        await asyncio.sleep(0.5)

      except Exception as e:
        self.logger.log_only('warning', f'Erreur d\'interaction non gérée : {e}')

  async def handle_view_response(self, interaction: discord.Interaction, content: str, view: discord.ui.View):
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
    
    
  async def handle_embed_response(self, interaction: discord.Interaction, embed: discord.Embed):
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
  
  async def handle_view_and_embed_response(self, interaction: discord.Interaction, embed: discord.Embed, view: discord.ui.View):
    if self.original_message_id and hasattr(interaction, 'message'):
      try:
        original_message = await interaction.channel.fetch_message(self.original_message_id)
        self.logger.log_only('debug', 'embed & view after modal with an original message')
        new_message = await original_message.edit(content='', embed=embed, view=view)
        self.original_message_id = None
        self.was_a_modal = False
        return new_message
      except Exception as e:
        self.logger.log_only('debug', f'erreur : {e}')

    if self.was_a_modal:
      try:
        self.logger.log_only('debug', 'embed & view after modal with no original message')
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