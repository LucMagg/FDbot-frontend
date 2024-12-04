import discord
import discord.ui
from discord.ext import commands
from discord import app_commands
from typing import Optional
from datetime import datetime, timezone

from service.interaction_handler import InteractionHandler
from service.command import CommandService

class Spire(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.interaction_handler = InteractionHandler(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'spire'), None)
    CommandService.init_command(self.spire_app_command, self.command)
    self.tiers = ['Platinum','Gold','Silver','Bronze','Hero','Adventurer']
    self.guilds = None

  class CommandData():
    def __init__(self):
      self.view = None
      self.selected_guild = None
      self.selected_tier = None
      self.selected_climb = None
      self.spire_data = None
      self.last_interaction = None
      self.handle_timeout = False

  class GuildModificationView(discord.ui.View):
##### VIEW DE VALIDATION DE LA GUILDE
    def __init__(self, outer, request_spire_data):
      outer.logger.log_only('debug', 'init guild modification view')
      super().__init__(timeout=180)
      self.outer = outer
      self.request_spire_data = request_spire_data

      self.guild_selector.options = [discord.SelectOption(label='Ajouter une nouvelle guilde', value='Ajouter une nouvelle guilde')]
      for g in self.outer.guilds:
        self.guild_selector.options.append(discord.SelectOption(label=g, value=g))
      self.guild_selector.placeholder = self.request_spire_data.selected_guild if self.request_spire_data.selected_guild else 'Ajouter une nouvelle guilde'

    @discord.ui.select(row=0, cls=discord.ui.Select) 
    async def guild_selector(self, interaction: discord.Interaction, select: discord.ui.Select):
      self.request_spire_data.selected_guild = self.guild_selector.values[0]
      self.guild_selector.placeholder = self.request_spire_data.selected_guild
      self.request_spire_data.last_interaction = interaction
      await interaction.response.defer()

    @discord.ui.button(row=1, style=discord.ButtonStyle.success, label='Suivant', custom_id='submit')
    async def go_to_guild_creation_or_tier_modification(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      if self.request_spire_data.selected_guild == 'Ajouter une nouvelle guilde':
        self.outer.logger.log_only('debug', 'nouvelle guilde')
        await self.outer.build_guild_creation_modal(interaction=interaction, request_spire_data=self.request_spire_data)
      else:
        self.request_spire_data.spire_data['guild'] = self.request_spire_data.selected_guild
        self.outer.logger.log_only('debug',f'guild: {self.request_spire_data.spire_data.get('guild')}')
        await self.outer.build_tier_modification_view(interaction=interaction, request_spire_data=self.request_spire_data)

    async def on_timeout(self):
      if self.request_spire_data.handle_timeout:
        self.outer.logger.log_only('debug', 'guild modification view timeout')
        await self.outer.interaction_handler.handle_response(interaction=self.request_spire_data.last_interaction, timeout=self.timeout)

  class GuildCreationModal(discord.ui.Modal, title='Création de guilde'):
##### MODALE DE CREATION DE GUILDE
    def __init__(self, outer, request_spire_data):
      outer.logger.log_only('debug', 'init guild creation modal')
      super().__init__(timeout=180)
      self.outer = outer
      self.request_spire_data = request_spire_data

    guild_name = discord.ui.TextInput(label='Entrez le nom de votre guilde', required=True, min_length=2, max_length=32)

    async def on_submit(self, interaction: discord.Interaction):
      self.stop()
      if self.does_guild_already_exist():
        await self.outer.build_guild_already_exists_view(interaction=interaction, request_spire_data=self.request_spire_data)
      else:
        self.request_spire_data.spire_data['guild'] = self.guild_name.value      
        await self.outer.build_tier_modification_view(interaction=interaction, request_spire_data=self.request_spire_data)

    def does_guild_already_exist(self):
      for g in self.outer.guilds:
        if self.guild_name.value.lower() == g.lower():
          self.request_spire_data.selected_guild = g
          return True
      return False
    
    async def on_timeout(self):
      if self.request_spire_data.handle_timeout:
        self.outer.logger.log_only('debug', 'guild creation modal timeout')
        self.stop()
        await self.outer.interaction_handler.handle_response(interaction=self.request_spire_data.last_interaction, timeout=self.timeout)
  class GuildAlreadyExistsView(discord.ui.View):
##### VIEW DE VALIDATION DE LA GUILDE DEJA EXISTANTE
    def __init__(self, outer, request_spire_data):
      outer.logger.log_only('debug', 'init guild already exists view')
      super().__init__(timeout=180)
      self.outer = outer
      self.request_spire_data = request_spire_data

    @discord.ui.button(style=discord.ButtonStyle.danger, label='Non', custom_id='no')
    async def back_to_guild_modification(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      await self.outer.build_guild_modification_view(interaction=interaction, request_spire_data=self.request_spire_data)

    @discord.ui.button(style=discord.ButtonStyle.success, label='Oui', custom_id='yes')
    async def go_to_tier_modification(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      self.request_spire_data.spire_data['guild'] = self.request_spire_data.selected_guild
      await self.outer.build_tier_modification_view(interaction=interaction, request_spire_data=self.request_spire_data)
    
    async def on_timeout(self):
      if self.request_spire_data.handle_timeout:
        self.outer.logger.log_only('debug', 'guild already exists view timeout')
        await self.outer.interaction_handler.handle_response(interaction=self.request_spire_data.last_interaction, timeout=self.timeout)

  class TierModificationView(discord.ui.View):
##### VIEW DE VALIDATION DU TIER
    def __init__(self, outer, request_spire_data):
      outer.logger.log_only('debug', 'init tier modification view')
      super().__init__(timeout=180)
      self.outer = outer
      self.request_spire_data = request_spire_data
      
      self.tier_selector.options = []
      for t in self.outer.tiers:
        self.tier_selector.options.append(discord.SelectOption(label=t, value=t))
      self.tier_selector.placeholder = self.request_spire_data.selected_tier if self.request_spire_data.selected_tier else 'Choisis ton tier'

      self.go_to_climb_modification.disabled = False if self.request_spire_data.selected_tier else True

    @discord.ui.select(cls=discord.ui.Select)
    async def tier_selector(self, interaction: discord.Interaction, select: discord.ui.Select): 
      self.request_spire_data.selected_tier = self.tier_selector.values[0]
      self.tier_selector.placeholder = self.request_spire_data.selected_tier
      self.go_to_climb_modification.disabled = False
      self.request_spire_data.last_interaction = interaction
      await self.outer.interaction_handler.handle_response(interaction=interaction, view=self)

    @discord.ui.button(style=discord.ButtonStyle.success, label='Suivant', custom_id='submit')
    async def go_to_climb_modification(self, interaction: discord.Interaction, button: discord.ui.Button):
      if self.request_spire_data.selected_tier:
        self.stop()
        self.request_spire_data.spire_data['tier'] = self.request_spire_data.selected_tier
        await self.outer.build_climb_modification_view(interaction=interaction, request_spire_data=self.request_spire_data)

    async def on_timeout(self):
      if self.request_spire_data.handle_timeout:
        self.outer.logger.log_only('debug', 'tier modification view timeout')
        await self.outer.interaction_handler.handle_response(interaction=self.request_spire_data.last_interaction, timeout=self.timeout)      

  class ClimbModificationView(discord.ui.View):
  ##### VIEW DE VALIDATION DU CLIMB
    def __init__(self, outer, request_spire_data):
      outer.logger.log_only('debug', 'init climb modification view')
      super().__init__(timeout=180)
      self.outer = outer
      self.request_spire_data = request_spire_data
      self.climb_selector.placeholder = str(self.request_spire_data.selected_climb) if self.request_spire_data.selected_climb else 'Choisis ton climb'
      self.go_to_score_modification.disabled = False if self.request_spire_data.selected_climb else True

    @discord.ui.select(cls=discord.ui.Select, options=[discord.SelectOption(label=str(t), value=str(t)) for t in range(1, 5)])
    async def climb_selector(self, interaction: discord.Interaction, select: discord.ui.Select):
      self.request_spire_data.selected_climb = int(self.climb_selector.values[0])
      self.climb_selector.placeholder = str(self.request_spire_data.selected_climb)
      self.go_to_score_modification.disabled = False
      self.request_spire_data.last_interaction = interaction
      await self.outer.interaction_handler.handle_response(interaction=interaction, view=self)

    @discord.ui.button(style=discord.ButtonStyle.success, label='Suivant', custom_id='submit')
    async def go_to_score_modification(self, interaction: discord.Interaction, button: discord.ui.Button):
      if self.request_spire_data.selected_climb:
        self.request_spire_data.spire_data['climb'] = self.request_spire_data.selected_climb
        await self.outer.build_score_modification_modal(interaction=interaction, request_spire_data=self.request_spire_data)

    async def on_timeout(self):
      if self.request_spire_data.handle_timeout:
        self.outer.logger.log_only('debug', 'climb modification view timeout')
        await self.outer.interaction_handler.handle_response(interaction=self.request_spire_data.last_interaction, timeout=self.timeout)

  class ScoreModificationModal(discord.ui.Modal):
##### MODALE DE MODIFICATION DU SCORE
    def __init__(self, outer, request_spire_data):
      outer.logger.log_only('debug', 'init score modification modal')
      super().__init__(title='Score', timeout=180)
      self.outer = outer
      self.request_spire_data = request_spire_data
      self.floors = discord.ui.TextInput(label='Étages terminés', default=str(self.request_spire_data.spire_data.get('floors')), required=True)
      self.add_item(self.floors)
      self.loss = discord.ui.TextInput(label='Héros perdus', default=str(self.request_spire_data.spire_data.get('loss')), required=True)
      self.add_item(self.loss)
      self.turns = discord.ui.TextInput(label='Tours joués', default=str(self.request_spire_data.spire_data.get('turns')), required=True)
      self.add_item(self.turns)
      self.bonus = discord.ui.TextInput(label='Bonus gagnés', default=str(self.request_spire_data.spire_data.get('bonus')), required=True)
      self.add_item(self.bonus)

    async def on_submit(self, interaction: discord.Interaction):
      self.stop()
      self.outer.logger.log_only('debug', 'modal submit')
      self.request_spire_data.spire_data['floors'] = self.is_input_valid(self.floors.value, 1, 14)
      self.request_spire_data.spire_data['loss'] = self.is_input_valid(self.loss.value, 0)
      self.request_spire_data.spire_data['turns'] = self.is_input_valid(self.turns.value, 31)
      self.request_spire_data.spire_data['bonus'] = self.is_input_valid(self.bonus.value, 0, 84)
      try:
        self.request_spire_data.spire_data['score'] = self.request_spire_data.spire_data.get('floors') * 50000 - self.request_spire_data.spire_data.get('loss') * 1000 - self.request_spire_data.spire_data.get('turns') * 100 + self.request_spire_data.spire_data.get('bonus') * 250
      except Exception as e:
        self.outer.logger.log_only('warning', f'modal submit error: {e}')
      if not None in self.request_spire_data.spire_data.values():
        await self.outer.build_validation_view(interaction=interaction, request_spire_data=self.request_spire_data)
      else:
        alert_message = '# Erreur ! #\n'
        if self.request_spire_data.spire_data.get('floors') is None:
          alert_message += 'Le nombre d\'étages terminés doit être compris entre 1 et 14 :wink:\n'
        if self.request_spire_data.spire_data.get('loss') is None:
          alert_message += 'Le nombre de héros perdus doit être supérieur ou égal à 0 :wink:\n'
        if self.request_spire_data.spire_data.get('turns') is None:
          alert_message += 'Le nombre de tours doit être supérieur ou égal à 31 :wink:\n'
        if self.request_spire_data.spire_data.get('bonus') is None:
          alert_message += 'Le nombre de bonus gagnés doit être compris entre 0 et 84 :wink:\n'
        alert_message += 'Merci de saisir des valeurs cohérentes :stuck_out_tongue:\n\n'
        alert_message += 'Voulez-vous corriger les erreurs de saisie ?'
        await self.outer.build_error_view(interaction=interaction, message=alert_message, request_spire_data=self.request_spire_data)

    def is_input_valid(self, to_check: str, min_value: int, max_value: Optional[int] = None):
      try:
        value = int(to_check)
      except:
        self.outer.logger.log_only('debug', f'Couldn\'t cast {to_check} to int')
        return None
      if value < min_value or max_value and value > max_value:
        self.outer.logger.log_only('debug', f'{value} not within [{min_value}, {max_value}]')
        return None
      return value
    
    async def on_timeout(self):
      if self.request_spire_data.handle_timeout:
        self.stop()
        self.outer.logger.log_only('debug', 'score modification modal timeout')
        await self.outer.interaction_handler.handle_response(interaction=self.request_spire_data.last_interaction, timeout=self.timeout)

  class ErrorView(discord.ui.View):
##### VIEW D'ERREUR
    def __init__(self, outer, request_spire_data):
      outer.logger.log_only('debug', 'init error view')
      super().__init__(timeout=180)
      self.outer = outer
      self.request_spire_data = request_spire_data

    @discord.ui.button(style=discord.ButtonStyle.success, label='Modifier', custom_id='modif')
    async def back_to_score_modification(self, interaction: discord.Interaction, button: discord.ui.Button):
      await self.outer.build_score_modification_modal(interaction=interaction, request_spire_data=self.request_spire_data)
        
    @discord.ui.button(style=discord.ButtonStyle.danger, label='Abandonner', custom_id='cancel')
    async def cancel_spire_command(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.request_spire_data.handle_timeout = False
      response = {'title': 'Abandon',
                  'description': 'La saisie de ton score de spire a bien été annulée :cry:\nN\'hésite pas à recommencer pour soutenir ta guilde :grin:',
                  'color': 'red'}
      await self.outer.interaction_handler.handle_response(interaction=interaction, response=response)
      self.outer.logger.ok_log('spire')
      
    async def on_timeout(self):
      if self.request_spire_data.handle_timeout:
        self.stop()
        self.outer.logger.log_only('debug', 'error view timeout')
        await self.outer.interaction_handler.handle_response(interaction=self.request_spire_data.last_interaction, timeout=self.timeout)

  class ValidationView(discord.ui.View):
##### VIEW DE VALIDATION FINALE
    def __init__(self, outer, request_spire_data):
      outer.logger.log_only('debug', 'init validation view')
      super().__init__(timeout=180)
      self.outer = outer
      self.request_spire_data = request_spire_data

    @discord.ui.button(style=discord.ButtonStyle.danger, label='Modifier', custom_id='modif')
    async def back_to_beginning(self, interaction: discord.Interaction, button: discord.ui.Button):
      await self.outer.build_guild_modification_view(interaction=interaction, request_spire_data=self.request_spire_data)
        
    @discord.ui.button(style=discord.ButtonStyle.success, label='Valider', custom_id='valid')
    async def go_to_the_end(self, interaction: discord.Interaction, button: discord.ui.Button):
      await self.outer.send_validation_message(interaction=interaction, request_spire_data=self.request_spire_data)

    async def on_timeout(self):
      if self.request_spire_data.handle_timeout:
        self.stop()
        self.outer.logger.log_only('debug', 'validation view timeout')
        await self.outer.interaction_handler.handle_response(interaction=self.request_spire_data.last_interaction, timeout=self.timeout)
  
  @app_commands.command(name='spire')
  async def spire_app_command(self, interaction: discord.Interaction, screenshot: discord.Attachment):
    self.logger.command_log('spire', interaction)
    self.logger.log_only('debug', f"arg : {screenshot.url}")
    await self.get_response(screenshot.url, interaction)

  async def get_response(self, image_url, interaction: discord.Interaction):
    request_spire_data = self.CommandData()
    request_spire_data.last_interaction = interaction
    request_spire_data.handle_timeout = True
    temp_spire_data = self.get_user_and_guildname(interaction=interaction)
    temp_spire_data['image_url'] = image_url
    request_spire_data.spire_data = await self.bot.back_requests.call('extractSpireData', False, [temp_spire_data])
    self.logger.log_only('debug', f'spire_data: {self.spire_data}')
    request_spire_data.selected_guild = request_spire_data.spire_data.get('guild')
    request_spire_data.selected_tier = request_spire_data.spire_data.get('tier')
    request_spire_data.selected_climb = request_spire_data.spire_data.get('climb')
    if request_spire_data.spire_data.get('guild') is not None and request_spire_data.spire_data.get('guild') not in self.guilds:
      self.guilds.append(request_spire_data.spire_data.get('guild'))
      self.guilds = sorted(self.guilds)
    if None in request_spire_data.spire_data.values():
      await self.build_guild_modification_view(interaction=interaction, request_spire_data=request_spire_data)
    else:
      await self.build_validation_view(interaction=interaction, request_spire_data=request_spire_data)

  def get_user_and_guildname(self, interaction: discord.Interaction):
    self.spire_data = None
    user = interaction.user.display_name
    self.logger.log_only('debug', f'user: {user}')
    if '[' in user and ']' in user:
      self.logger.log_only('debug', 'user & guild ok')
      username = user.split('[')[0].strip()
      guild = user.split('[')[1]
      if guild[-1] == ']':
        guild = guild[:-1]
      elif username == '':
        username = user.split(']')[1].strip()
        guild = user.split('[')[1].split(']')[0].strip()
      else:
        guild = f'[{guild}'
      self.logger.log_only('debug', f'username: {username}')
      self.logger.log_only('debug', f'guild: {guild}')
      return {'username': username, 'guild': guild}
    else:
      self.logger.log_only('debug', 'user only')
      return {'username': user, 'guild': None}

  async def build_guild_modification_view(self, interaction: discord.Interaction, request_spire_data: CommandData):
    request_spire_data.last_interaction = interaction
    view = self.GuildModificationView(outer=self, request_spire_data=request_spire_data)
    content = '# Guilde #\nVeuillez choisir votre guilde ou en créer une nouvelle si la vôtre n\'est pas dans la liste :'
    await self.interaction_handler.handle_response(interaction=interaction, content=content, view=view)

  async def build_guild_creation_modal(self, interaction: discord.Interaction, request_spire_data: CommandData):
    request_spire_data.last_interaction = interaction
    modal = self.GuildCreationModal(outer=self, request_spire_data=request_spire_data)
    await self.interaction_handler.handle_response(interaction=interaction, modal=modal)

  async def build_guild_already_exists_view(self, interaction: discord.Interaction, request_spire_data: CommandData):
    request_spire_data.last_interaction = interaction
    view = self.GuildAlreadyExistsView(outer=self, request_spire_data=request_spire_data)
    content = f'# {request_spire_data.selected_guild} #\nCette guilde existe déjà...\nVoulez-vous valider ?'
    await self.interaction_handler.handle_response(interaction=interaction, content=content, view=view)

  async def build_tier_modification_view(self, interaction: discord.Interaction, request_spire_data: CommandData):
    request_spire_data.last_interaction = interaction
    view = self.TierModificationView(outer=self, request_spire_data=request_spire_data)
    content = '# Dragonspire Tier #\nChoisissez votre niveau de spire parmi les suivants :'
    await self.interaction_handler.handle_response(interaction=interaction, content=content, view=view)

  async def build_climb_modification_view(self, interaction: discord.Interaction, request_spire_data: CommandData):
    request_spire_data.last_interaction = interaction
    view = self.ClimbModificationView(outer=self, request_spire_data=request_spire_data)
    content = '# Climb #\nChoisissez le climb parmi les suivants :'
    await self.interaction_handler.handle_response(interaction=interaction, content=content, view=view)

  async def build_score_modification_modal(self, interaction: discord.Interaction, request_spire_data: CommandData):
    request_spire_data.last_interaction = interaction
    modal = self.ScoreModificationModal(outer=self, request_spire_data=request_spire_data)
    await self.interaction_handler.handle_response(interaction=interaction, modal=modal)

  async def build_error_view(self, interaction: discord.Interaction, message: str, request_spire_data: CommandData):
    request_spire_data.last_interaction = interaction
    view = self.ErrorView(outer=self, request_spire_data=request_spire_data)
    await self.interaction_handler.handle_response(interaction=interaction, content=message, view=view)

  async def build_validation_view(self, interaction: discord.Interaction, request_spire_data: CommandData):
    request_spire_data.last_interaction = interaction
    self.logger.log_only('debug', f'spire_data: {request_spire_data.spire_data}')
    view = self.ValidationView(outer=self, request_spire_data=request_spire_data)
    content = self.build_validation_content(request_spire_data=request_spire_data)
    await self.interaction_handler.handle_response(interaction=interaction, content=content, view=view)

  def build_validation_content(self, request_spire_data: CommandData):
    request_spire_data.spire_data['score'] = request_spire_data.spire_data.get('floors') * 50000 - request_spire_data.spire_data.get('loss') * 1000 - request_spire_data.spire_data.get('turns') * 100 + request_spire_data.spire_data.get('bonus') * 250
    to_return = '# Validation du score #\n'
    to_return += f'Vous êtes sur le point de valider votre score de spire avec les informations suivantes :\n'
    to_return += f'\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0• Guilde : {request_spire_data.spire_data.get('guild')}\n'
    to_return += f'\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0• Tier : {request_spire_data.spire_data.get('tier')}\n'
    to_return += f'\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0• Climb : {request_spire_data.spire_data.get('climb')}\n'
    to_return += f'\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0• Score : {request_spire_data.spire_data.get('score')}\n'
    return to_return

  async def send_validation_message(self, interaction: discord.Interaction, request_spire_data: CommandData):
    request_spire_data.handle_timeout = False
    post_spire = await self.bot.back_requests.call('addSpireData', False, [request_spire_data.spire_data])
    if not post_spire:
      await self.interaction_handler.handle_response(interaction=interaction, response={'title': 'Erreur !', 'description': 'Ton score n\'a pas pu être ajouté :cry:\nMerci de réitérer la commande :innocent:', 'color': 'red'})
      self.logger.ok_log('spire')
      return
    description = '# Score validé ! #\n'
    description += f'Merci pour ta participation {request_spire_data.spire_data.get('username')} :wink:\n\n'
    description += await self.bot.spire_service.display_scores_after_posting_spire(tier=request_spire_data.spire_data.get('tier'))
    response = {'title': '', 'description': description, 'color': 'blue', 'image': request_spire_data.spire_data.get('image_url')}
    await self.interaction_handler.handle_response(interaction=interaction, response=response)
    if request_spire_data.spire_data.get('guild') not in self.guilds:
      self.logger.log_only('debug', 'add new guild to self.guilds')
      self.guilds.append(request_spire_data.spire_data.get('guild'))
      self.guilds = sorted(self.guilds)
    add_channel_data = {'date': datetime.now(tz=timezone.utc).isoformat(), 'channel_id': interaction.channel_id, 'guild': request_spire_data.spire_data.get('guild')}
    await self.bot.back_requests.call('addChannelToSpire', False, [add_channel_data])
    await self.setup()
    self.logger.ok_log('spire')

  async def setup(self, param_list=None):
    try:
      if param_list is None:
        guilds = await self.bot.back_requests.call('getAllExistingGuilds', False)
      else:
        guilds = param_list
      self.guilds = [guild.get('name') for guild in guilds] if guilds else []
    except Exception as e:
      self.logger.log_only('warning', f'spire setup error: {e}')

async def setup(bot):
  await bot.add_cog(Spire(bot))