import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from utils.sendMessage import SendMessage
from utils.misc_utils import get_discord_color
from service.command import CommandService

class Spire(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'spire'), None)

    self.command_service = CommandService()
    CommandService.init_command(self.spire_app_command, self.command)

    self.guilds = None
    self.tiers = ['Platinum','Gold','Silver','Bronze','Hero','Adventurer']
    self.selected_guild = None
    self.selected_tier = None
    self.spire_data = None
    self.send_spire_results.start()

  class GuildModificationView(discord.ui.View):
##### VIEW DE VALIDATION DE LA GUILDE
    def __init__(self, outer):
      print('init guild modification view begin')
      super().__init__(timeout=180)
      self.outer = outer
      try:
        self.add_item(self.outer.GuildSelector(outer=self.outer))
        self.add_item(self.outer.GuildNextButton(outer=self.outer))
      except Exception as e:
        print(f'erreur: {e}')
      print('init guild modification view end')

  class GuildSelector(discord.ui.Select):
    def __init__(self, outer):
      print('init guild selector begin')
      try:
        self.outer = outer
        options = [discord.SelectOption(label='Ajouter une nouvelle guilde', value='Ajouter une nouvelle guilde')]
        for g in self.outer.guilds:
          options.append(discord.SelectOption(label=g, value=g))

        if self.outer.selected_guild is not None:
          guild = self.outer.selected_guild
          if guild != 'Ajouter une nouvelle guilde' and guild not in self.outer.guilds:
            options.append(discord.SelectOption(label=guild, value=guild))

        placeholder = self.outer.selected_guild if self.outer.selected_guild else 'Ajouter une nouvelle guilde'
        self.outer.selected_guild = placeholder
        super().__init__(custom_id='selector', placeholder=placeholder, options=options)

      except Exception as e:
        print(f'guildselector erreur: {e}')
      print('init guild selector end')

    async def callback(self, interaction: discord.Interaction):
      try:
        print(f'select: {self.values[0]}')
        self.outer.selected_guild = self.values[0]
        await self.outer.build_guild_modification_view(interaction)
      except Exception as e:
        print(f'guildselector erreur: {e}')

  class GuildNextButton(discord.ui.Button):
    def __init__(self, outer):
      print('init next button begin')
      self.outer = outer
      super().__init__(style=discord.ButtonStyle.success, label='Suivant', custom_id='submit')
      print('init next button end')

    async def callback(self, interaction: discord.Interaction):
      if self.outer.selected_guild == 'Ajouter une nouvelle guilde':
        print('nouvelle guilde')
        await self.outer.build_guild_creation_modal(interaction)
      else:
        self.outer.spire_data['guild'] = self.outer.selected_guild
        print(f'guild: {self.outer.spire_data.get('guild')}')
        await self.outer.build_tier_modification_view(interaction)

  class GuildCreationModal(discord.ui.Modal):
##### MODALE DE CREATION DE GUILDE
    def __init__(self, outer):
      super().__init__(title='Création de guilde', timeout=180)
      self.outer = outer
      self.input_guild = self.outer.InputGuild()
      self.add_item(self.input_guild)

    async def on_submit(self, interaction: discord.Interaction):
      if self.does_guild_already_exist():
        await self.outer.build_guild_already_exists_view(interaction)
      else:
        self.outer.spire_data['guild'] = self.outer.selected_guild
        await self.outer.build_tier_modification_view(interaction)

    def does_guild_already_exist(self):
      for g in self.outer.guilds:
        if self.input_guild.value.lower() == g.lower():
          self.outer.selected_guild = g
          return True
      return False

  class InputGuild(discord.ui.TextInput):
    def __init__(self):
      super().__init__(label='Entrez le nom de votre guilde', custom_id='input', required=True, min_length=2, max_length=32)

  class GuildAlreadyExistsView(discord.ui.View):
##### VIEW DE VALIDATION DE LA GUILDE DEJA EXISTANTE
    def __init__(self, outer):
      print('init guild already exists view begin')
      super().__init__(timeout=180)
      self.outer = outer
      self.add_item(self.outer.NoButton(outer=self.outer))
      self.add_item(self.outer.YesButton(outer=self.outer))
      print('init guild already exists view end')

  class NoButton(discord.ui.Button):
    def __init__(self, outer):
      print('init no button begin')
      self.outer = outer
      super().__init__(style=discord.ButtonStyle.danger, label='Non', custom_id='no')
      print('init no button end')

    async def callback(self, interaction: discord.Interaction):
      await self.outer.build_guild_modification_view(interaction)

  class YesButton(discord.ui.Button):
    def __init__(self, outer):
      print('init yes button begin')
      self.outer = outer
      super().__init__(style=discord.ButtonStyle.success, label='Oui', custom_id='yes')
      print('init yes button end')

    async def callback(self, interaction: discord.Interaction):
      self.outer.spire_data['guild'] = self.outer.selected_guild
      await self.outer.build_tier_modification_view(interaction)

  class TierModificationView(discord.ui.View):
##### VIEW DE VALIDATION DU TIER
    def __init__(self, outer):
      print('init tier modification view begin')
      super().__init__(timeout=180)
      self.outer = outer
      try:
        self.add_item(self.outer.TierSelector(outer=self.outer))
        self.add_item(self.outer.TierNextButton(outer=self.outer))
      except Exception as e:
        print(f'erreur: {e}')
      print('init tier modification view end')

  class TierSelector(discord.ui.Select):
    def __init__(self, outer):
      print('init tier selector begin')
      try:
        self.outer = outer
        options = []
        for t in self.outer.tiers:
          options.append(discord.SelectOption(label=t, value=t))
        placeholder = self.outer.selected_tier
        super().__init__(custom_id='selector', placeholder=placeholder, options=options)

      except Exception as e:
        print(f'tierselector erreur: {e}')
      print('init tier selector end')

    async def callback(self, interaction: discord.Interaction):
      try:
        print(f'select: {self.values[0]}')
        self.outer.selected_tier = self.values[0]
        await self.outer.build_tier_modification_view(interaction)
      except Exception as e:
        print(f'tierselector erreur: {e}')

  class TierNextButton(discord.ui.Button):
    def __init__(self, outer):
      print('init next button begin')
      self.outer = outer
      super().__init__(style=discord.ButtonStyle.success, label='Suivant', custom_id='submit')
      print('init next button end')

    async def callback(self, interaction: discord.Interaction):
      self.outer.spire_data['tier'] = self.outer.selected_tier
      await self.outer.build_score_modification_modal(interaction)

  class ScoreModificationModal(discord.ui.Modal):
##### MODALE DE MODIFICATION DU SCORE
    def __init__(self, outer):
      super().__init__(title='Score', timeout=180)
      self.outer = outer
      self.input_floors = self.outer.InputScore(label='Étages terminés', default=str(self.outer.spire_data.get('floors')))
      self.add_item(self.input_floors)
      self.input_loss = self.outer.InputScore(label='Héros perdus', default=str(self.outer.spire_data.get('loss')))
      self.add_item(self.input_loss)
      self.input_turns = self.outer.InputScore(label='Tours joués', default=str(self.outer.spire_data.get('turns')))
      self.add_item(self.input_turns)
      self.input_bonus = self.outer.InputScore(label='Bonus gagnés', default=str(self.outer.spire_data.get('bonus')))
      self.add_item(self.input_bonus)

    async def on_submit(self, interaction: discord.Interaction):
      print('modal submit')

      self.outer.spire_data['floors'] = self.is_input_valid(self.input_floors.value, 1, 14)
      self.outer.spire_data['loss'] = self.is_input_valid(self.input_loss.value, 0)
      self.outer.spire_data['turns'] = self.is_input_valid(self.input_turns.value, 31)
      self.outer.spire_data['bonus'] = self.is_input_valid(self.input_bonus.value, 0, 84)
      if not None in self.outer.spire_data.values():
        await self.outer.build_validation_view(interaction)
      else:
        alert_message = '# Erreur ! #\n'
        if self.outer.spire_data.get('floors') is None:
          alert_message += 'Le nombre d\'étages terminés doit être compris entre 1 et 14 :wink:\n'
        if self.outer.spire_data.get('loss') is None:
          alert_message += 'Le nombre de héros perdus doit être supérieur ou égal à 0 :wink:\n'
        if self.outer.spire_data.get('turns') is None:
          alert_message += 'Le nombre de tours doit être supérieur ou égal à 31 :wink:\n'
        if self.outer.spire_data.get('bonus') is None:
          alert_message += 'Le nombre de bonus gagnés doit être compris entre 0 et 84 :wink:\n'
        alert_message += 'Merci de saisir des valeurs cohérentes :stuck_out_tongue:\n\n'
        alert_message += 'Voulez-vous corriger les erreurs de saisie ?'
        await self.outer.build_error_view(interaction, alert_message)

    def is_input_valid(self, to_check: str, min_value: int, max_value: Optional[int] = None):
      try:
        print(f'check: {to_check}')
        value = int(to_check)
      except:
        print(f'Couldn\'t cast {to_check} to int')

        return None
      if value < min_value or max_value and value > max_value:
        print(f'{value} not within [{min_value}, {max_value}]')
        return None
      return value

  class InputScore(discord.ui.TextInput):
    def __init__(self, label, default):
      super().__init__(label=label, default=default, required=True)

  class ErrorView(discord.ui.View):
##### VIEW D'ERREUR
    def __init__(self, outer):
      print('init error view begin')
      super().__init__(timeout=180)
      self.outer = outer
      try:
        self.add_item(self.outer.ErrorCancelButton(outer=self.outer))
        self.add_item(self.outer.ErrorModifButton(outer=self.outer))
      except Exception as e:
        print(f'erreur: {e}')
      print('init error view end')

  class ErrorCancelButton(discord.ui.Button):
    def __init__(self, outer):
      print('init cancel button begin')
      self.outer = outer
      super().__init__(style=discord.ButtonStyle.danger, label='Abandonner', custom_id='cancel')
      print('init cancel button end')

    async def callback(self, interaction: discord.Interaction):
      response = {'title': 'Abandon', 'description': 'La saisie de ton score de spire a bien été annulée :cry:\nN\'hésite pas à recommencer pour soutenir ta guilde :grin:', 'color': 'red'}
      await self.outer.send_message.update_remove_view(interaction, response)
      self.outer.logger.ok_log('spire')

  class ErrorModifButton(discord.ui.Button):
    def __init__(self, outer):
      print('init valid button begin')
      self.outer = outer
      super().__init__(style=discord.ButtonStyle.success, label='Modifier', custom_id='modif')
      print('init valid button end')

    async def callback(self, interaction: discord.Interaction):
      await self.outer.build_score_modification_modal(interaction)

  class ValidationView(discord.ui.View):
##### VIEW DE VALIDATION FINALE
    def __init__(self, outer):
      print('init validation view begin')
      super().__init__(timeout=180)
      self.outer = outer
      try:
        self.add_item(self.outer.ValidationModifButton(outer=self.outer))
        self.add_item(self.outer.ValidationOkButton(outer=self.outer))
      except Exception as e:
        print(f'erreur: {e}')
      print('init validation view end')

  class ValidationModifButton(discord.ui.Button):
    def __init__(self, outer):
      print('init modif button begin')
      self.outer = outer
      super().__init__(style=discord.ButtonStyle.danger, label='Modifier', custom_id='modif')
      print('init modif button end')

    async def callback(self, interaction: discord.Interaction):
      await self.outer.build_guild_modification_view(interaction)

  class ValidationOkButton(discord.ui.Button):
    def __init__(self, outer):
      print('init valid button begin')
      self.outer = outer
      super().__init__(style=discord.ButtonStyle.success, label='Valider', custom_id='valid')
      print('init valid button end')

    async def callback(self, interaction: discord.Interaction):
      await self.outer.send_validation_message(interaction)

  class ResponseManager:
##### GESTION DES INTERACTIONS
    def __init__(self):
      self.initial_interaction = None
      self.last_content = None

    async def handle_response(self, interaction: discord.Interaction, response=None, content='', view=None, modal=None, ephemeral=False):
      try:
        if response is not None:
          embed = discord.Embed(title=response.get('title'), description=response.get('description'), color=get_discord_color(response.get('color')))
        else:
          embed = None
        if modal is not None:
          await interaction.response.send_modal(modal)
        else:
          if self.initial_interaction is None:
            self.initial_interaction = interaction
            if view is None:
              await interaction.response.send_message(content=content, embed=embed)
            else:
              await interaction.response.send_message(content=content, embed=embed, view=view)
              self.last_content = content
          else:
            if view is None:
              try:
                await interaction.response.edit_message(content='', embed=embed, view=None)
              except Exception as e:
                print(f'Erreur : {e}\n-> envoi d\'une nouvelle interaction')
                interaction.response.send_message(content='', embed=embed, view=None)
            else:
              if content == '':
                content = self.last_content
              await interaction.response.edit_message(content=content, embed=embed, view=view)
              self.last_content = content

      except Exception as e:
        print(f"Une erreur s'est produite : {e}")

  @app_commands.command(name='spire')
  async def spire_app_command(self, interaction: discord.Interaction, screenshot: discord.Attachment):
    self.logger.command_log('spire', interaction)
    self.logger.log_only('debug', f"arg : {screenshot.url}")
    await self.get_response(screenshot.url, interaction)

  async def get_response(self, image_url, interaction: discord.Interaction):
    self.spire_data = self.get_user_and_guildname(interaction)
    self.response_manager = self.ResponseManager()
    self.spire_data['image_url'] = image_url
    self.spire_data = await self.bot.back_requests.call('extractSpireData', False, [self.spire_data])
    print(f'spire_data: {self.spire_data}')
    self.selected_guild = self.spire_data.get('guild')
    self.selected_tier = self.spire_data.get('tier')
    if self.spire_data.get('guild') is not None and self.spire_data.get('guild') not in self.guilds:
      self.guilds.append(self.spire_data.get('guild'))
      self.guilds = sorted(self.guilds)

    if None in self.spire_data.values():
      await self.build_guild_modification_view(interaction)
    else:
      await self.build_validation_view(interaction)

  def get_user_and_guildname(self, interaction: discord.Interaction):
    self.spire_data = None
    full_user = interaction.user.nick
    print(f'user: {full_user}')
    if full_user is None:
      print('user not defined -> user.name')
      return {'username': interaction.user.name, 'guild': None}
    else:
      if '[' in full_user and ']' in full_user:
        print('user & guild ok')
        username = full_user.split('[')[0].strip()
        guild = full_user.split('[')[1].split(']')[0]
        if username == '':
          username = full_user.split(']')[1].strip()
        print(f'username: {username}')
        print(f'guild: {guild}')
        return {'username': username, 'guild': guild}
      else:
        print('user only')
        return {'username': full_user, 'guild': None}

  async def build_guild_modification_view(self, interaction: discord.Interaction):
    self.view = self.GuildModificationView(self)
    content = '# Guilde #\nVeuillez choisir votre guilde ou en créer une nouvelle si la vôtre n\'est pas dans la liste :'
    await self.response_manager.handle_response(interaction=interaction, content=content, view=self.view)

  async def build_guild_creation_modal(self, interaction: discord.Interaction):
    self.modal = self.GuildCreationModal(self)
    await self.response_manager.handle_response(interaction=interaction, modal=self.modal)

  async def build_guild_already_exists_view(self, interaction: discord.Interaction):
    self.view = self.GuildAlreadyExistsView(self)
    content = f'# {self.selected_guild} #\nCette guilde existe déjà...\nVoulez-vous valider ?'
    await self.response_manager.handle_response(interaction=interaction, content=content, view=self.view)

  async def build_tier_modification_view(self, interaction: discord.Interaction):
    self.view = self.TierModificationView(self)
    content = '# Dragonspire Tier #\nChoisissez votre niveau de spire parmi les suivants :'
    await self.response_manager.handle_response(interaction=interaction, content=content, view=self.view)

  async def build_score_modification_modal(self, interaction: discord.Interaction):
    self.modal = self.ScoreModificationModal(self)
    await self.response_manager.handle_response(interaction=interaction, modal=self.modal)

  async def build_error_view(self, interaction: discord.Interaction, message):
    self.view = self.ErrorView(self)
    await self.response_manager.handle_response(interaction=interaction, content=message, view=self.view)

  async def build_validation_view(self, interaction: discord.Interaction):
    self.modal = None
    self.view = self.ValidationView(self)
    content = self.build_validation_content()
    await self.response_manager.handle_response(interaction=interaction, content=content, view=self.view)

  def build_validation_content(self):
    self.spire_data['score'] = self.spire_data.get('floors') * 50000 - self.spire_data.get('loss') * 1000 - self.spire_data.get('turns') * 100 + self.spire_data.get('bonus') * 250
    to_return = '# Validation du score #\n'
    to_return += f'Vous êtes sur le point de valider votre score de spire avec les informations suivantes :\n'
    to_return += f'\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0• Guilde : {self.spire_data.get('guild')}\n'
    to_return += f'\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0• Tier : {self.spire_data.get('tier')}\n'
    to_return += f'\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0• Climb : {self.spire_data.get('climb')}\n'
    to_return += f'\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0• Score : {self.spire_data.get('score')}\n'
    return to_return

  async def send_validation_message(self, interaction: discord.Interaction):
    post_spire = await self.bot.back_requests.call('addSpireData', False, [self.spire_data])

    if not post_spire:
      await self.send_message.update_remove_view(interaction, {'title': 'Erreur !', 'description': 'Ton score n\'a pas pu être ajouté :cry:\nMerci de réitérer la commande :innocent:', 'color': 'red'})
      self.logger.ok_log('spire')
      return
    
    add_channel_data = {'date': '2024-11-03T15:00:00', 'channel_id': interaction.channel_id, 'guild': self.spire_data.get('guild')}
    print(add_channel_data)
    await self.bot.back_requests.call('addChannelToSpire', False, [add_channel_data])

    description = '# Score validé ! #\n'
    description += f'Merci pour ta participation {self.spire_data.get('username')} :wink:\n\n'
    description += await self.bot.spire_service.display_scores_after_posting_spire(tier=self.spire_data.get('tier'))
    response = {'title': '', 'description': description, 'color': 'blue', 'image': self.spire_data.get('image_url')}
    await self.send_message.update_remove_view(interaction, response)
    self.logger.ok_log('spire')

  async def setup(self, param_list):
    if param_list is None:
      guilds = await self.bot.back_requests.call('getAllExistingGuilds', False)
    else:
      guilds = param_list
    self.guilds = [guild.get('name') for guild in guilds]

async def setup(bot):
  await bot.add_cog(Spire(bot))
