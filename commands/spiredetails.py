import discord
import discord.ui
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import copy

from service.interaction_handler import InteractionHandler
from service.command import CommandService


class Spiredetails(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.command = next((c for c in bot.static_data.commands if c['name'] == 'spiredetails'), None)
    #self.help_msg = Message(bot).help('spiredetails')
  
    CommandService.init_command(self.spiredetails_app_command, self.command)
    self.maps = None
    self.detail_options = [{'label': 'Map du climb', 'key': 'map'}, 
                           {'label':'Bonus des héros', 'key': 'hero_bonus'}, 
                           {'label': 'Bonus des monstres', 'key': 'monster_bonus'}, 
                           {'label': 'Talents par floor', 'key': 'talents'}]
    self.hero_bonus_choices = None
    self.monster_bonus_choices = None
    self.buff_choices = None
    self.tiers = ['Platinum','Gold','Silver','Bronze','Hero','Adventurer']
    self.max_talents_floor = 13
    self.final_embed = None

  class CommandData():
    def __init__(self):
      self.spire = None
      self.climb = None
      self.view = None
      self.selected_map_pic = None
      self.last_interaction = None
      self.handle_timeout = False
      self.selected_details = None
      self.selected_tier = None
      self.selected_map = None

  class InitialView(discord.ui.View):
##### VIEW INITIALE
    def __init__(self, outer, request_spiredetails_data):
      outer.logger.log_only('debug', 'init initial view')
      super().__init__(timeout=180)
      self.outer = outer
      self.request_spiredetails_data = request_spiredetails_data
      self.selected_value = None
      self.update_selector_options()
      self.check_buttons_activation()

    @discord.ui.select(row=0, cls=discord.ui.Select, placeholder="Sélectionnez une option") 
    async def choice_selector(self, interaction: discord.Interaction, select: discord.ui.Select):
      self.selected_value = select.values[0]
      self.check_buttons_activation()
      self.request_spiredetails_data.last_interaction = interaction
      self.update_selector_options()
      await self.outer.interaction_handler.send_view(interaction=interaction, view=self)

    @discord.ui.button(row=1, style=discord.ButtonStyle.danger, label='Annuler')
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      self.request_spiredetails_data.last_interaction = interaction
      await self.outer.build_cancel_response(self.request_spiredetails_data)

    @discord.ui.button(row=1, style=discord.ButtonStyle.primary, label='Modifier')
    async def change_button(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      self.request_spiredetails_data.last_interaction = interaction
      match self.choice_selector.values[0]:
        case 'Map du climb':
          await self.outer.build_map_view(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)
        case 'Bonus des héros':
          await self.outer.build_hero_bonus_modal(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)
        case 'Bonus des monstres':
          await self.outer.build_monster_bonus_modal(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)
        case 'Talents par floor':
          await self.outer.build_bracket_view(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)
    
    @discord.ui.button(row=1, style=discord.ButtonStyle.success, label='Terminer')
    async def validate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      self.request_spiredetails_data.last_interaction = interaction
      await self.outer.build_final_view(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)

    def check_buttons_activation(self):
      self.change_button.disabled = (self.selected_value is None)
      print(f'Modif {"disabled" if self.selected_value is None else "enabled"}')
      self.validate_button.disabled = not any(self.request_spiredetails_data.selected_details.get(choice.get('key')) for choice in self.outer.detail_options)
      print(f'Terminer {"disabled" if self.validate_button.disabled else "enabled"}')
      
    def update_selector_options(self):
      self.choice_selector.options = []
      for choice in self.outer.detail_options:
        if self.request_spiredetails_data.selected_details.get(choice.get('key')):
          emoji = '🟢'
        else:
          emoji = '🔴'
        default = (self.selected_value == choice.get('label'))
        self.choice_selector.options.append(discord.SelectOption(label=choice.get('label'), value=choice.get('label'), emoji=emoji, default=default))

    async def on_timeout(self):
      if self.request_spiredetails_data.handle_timeout:
        self.outer.logger.log_only('debug', 'initial view timeout')
        await self.outer.interaction_handler.send_timeout_message(interaction=self.request_spiredetails_data.last_interaction, timeout=self.timeout)

  class MapView(discord.ui.View):
##### VIEW DE SELECTION DE LA MAP
    def __init__(self, outer, request_spiredetails_data):
      outer.logger.log_only('debug', 'init map view')
      super().__init__(timeout=180)
      self.outer = outer
      self.request_spiredetails_data = request_spiredetails_data
      self.set_map_selector_options()
      self.update_validate_button_label()
      
    @discord.ui.select(row=0, cls=discord.ui.Select) 
    async def map_selector(self, interaction: discord.Interaction, select: discord.ui.Select):
      selected_value = select.values[0]
      self.request_spiredetails_data.last_interaction = interaction
      if selected_value != 'Choisir la map':
        selected_map = next((m for m in self.outer.maps if m['name'] == selected_value), None)
        self.request_spiredetails_data.selected_map = selected_map
        self.request_spiredetails_data.selected_map_pic = self.outer.bot.map_service.generate_map(selected_map)
        print(f'file {self.request_spiredetails_data.selected_map_pic.filename} OK')
        print(f'selected map: {selected_value}')
        self.map_selector.placeholder = selected_value
        for option in self.map_selector.options:
          option.default = (option.value == selected_value)
        self.update_validate_button_label()
        await self.outer.interaction_handler.send_view_with_file(interaction=interaction, view=self, file=self.request_spiredetails_data.selected_map_pic)
      else:
        await interaction.response.defer()

    @discord.ui.button(row=1, style=discord.ButtonStyle.danger, label='Annuler')
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      self.request_spiredetails_data.last_interaction = interaction
      await self.outer.build_initial_view(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)

    @discord.ui.button(row=1, style=discord.ButtonStyle.success, label='Valider')
    async def validate_or_next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      self.request_spiredetails_data.last_interaction = interaction
      self.request_spiredetails_data.selected_details['map'] = self.request_spiredetails_data.selected_map
      if self.request_spiredetails_data.selected_map.get('has_water_or_lava'):
        await self.outer.build_water_or_lava_view(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)
      else:
        await self.outer.build_initial_view(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)

    def set_map_selector_options(self):
      selected_map = self.request_spiredetails_data.selected_details.get('map')
      selected_name = selected_map.get('name') if selected_map else None
      options = [discord.SelectOption(label=m.get('name'), value=m.get('name'), default=(m.get('name') == selected_name)) for m in self.outer.maps]
      options = sorted(options, key=lambda o: o.label)
      options.insert(0, discord.SelectOption(label='Choisir la map', value='Choisir la map', default=(selected_name is None)))
      self.map_selector.options = options
      self.map_selector.placeholder = selected_name or 'Choisir la map'

    def update_validate_button_label(self):
        selected_map = self.request_spiredetails_data.selected_map
        if selected_map:
          label = 'Suivant' if selected_map.get('has_water_or_lava') else 'Valider'
          self.validate_or_next_button.label = label

    async def on_timeout(self):
      if self.request_spiredetails_data.handle_timeout:
        self.outer.logger.log_only('debug', 'map view timeout')
        await self.outer.interaction_handler.send_timeout_message(interaction=self.request_spiredetails_data.last_interaction, timeout=self.timeout)

  class WaterOrLavaView(discord.ui.View):
##### VIEW DE SELECTION DE LA MAP
    def __init__(self, outer, request_spiredetails_data):
      outer.logger.log_only('debug', 'init water or lava view')
      super().__init__(timeout=180)
      self.outer = outer
      self.request_spiredetails_data = request_spiredetails_data

    @discord.ui.button(style=discord.ButtonStyle.primary, label='Eau')
    async def water_button(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      self.request_spiredetails_data.last_interaction = interaction
      self.request_spiredetails_data.selected_details['map']['water_or_lava'] = 'water'
      await self.outer.build_initial_view(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)

    @discord.ui.button(style=discord.ButtonStyle.danger, label='Lave')
    async def lava_button(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      self.request_spiredetails_data.last_interaction = interaction
      self.request_spiredetails_data.selected_details['map']['water_or_lava'] = 'lava'
      await self.outer.build_initial_view(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)


  class HeroBonusModal(discord.ui.Modal):
##### MODALE DE SAISIE DES BONUS DE HEROS
    def __init__(self, outer, request_spiredetails_data):
      outer.logger.log_only('debug', 'init hero bonus modal')
      super().__init__(title='Bonus des héros', timeout=180)
      self.outer = outer
      self.request_spiredetails_data = request_spiredetails_data
      
      self.hero_bonus_type_field = self.create_text_input(label='+250 score for each [XXX] in team', key='type', default='Entrez ici ce qui correspond à XXX')
      self.hero_bonus_buff_field = self.create_text_input(label='All [XXX] gain [YYY]', key='buff', default='Entrez ici ce qui correspond à YYY')

    async def on_submit(self, interaction: discord.Interaction):
      self.stop()
      self.outer.logger.log_only('debug', 'modal submit')
      if 'hero_bonus' not in self.request_spiredetails_data.selected_details:
        self.request_spiredetails_data.selected_details['hero_bonus'] = {}
      if self.hero_bonus_type_field.value != 'Entrez ici ce qui correspond à XXX':
        print(self.hero_bonus_type_field.value)
        self.request_spiredetails_data.selected_details['hero_bonus']['type'] = self.hero_bonus_type_field.value
      if self.hero_bonus_buff_field.value != 'Entrez ici ce qui correspond à YYY':
        print(self.hero_bonus_buff_field.value)
        self.request_spiredetails_data.selected_details['hero_bonus']['buff'] = self.hero_bonus_buff_field.value
      await self.outer.build_hero_bonus_validation_view(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)

    def create_text_input(self, label, key, default):
      hero_bonus = self.request_spiredetails_data.selected_details.get('hero_bonus', {})
      value = hero_bonus.get(key, default)
      print(f'hero_bonus_{key}: {value}')
      text_input = discord.ui.TextInput(label=label, placeholder=value, required=False)
      self.add_item(text_input)
      return text_input
    
    async def on_timeout(self):
      if self.request_spiredetails_data.handle_timeout:
        self.stop()
        self.outer.logger.log_only('debug', 'hero bonus modal timeout')
        await self.outer.interaction_handler.send_timeout_message(interaction=self.request_spiredetails_data.last_interaction, timeout=self.timeout)

  class YesNoView(discord.ui.View):
##### VIEW DE VALIDATION OUI/NON
    def __init__(self, outer, request_spiredetails_data, whichone):
      outer.logger.log_only('debug', 'init yes/no view')
      super().__init__(timeout=180)
      self.outer = outer
      self.request_spiredetails_data = request_spiredetails_data
      self.whichone = whichone

    @discord.ui.button(style=discord.ButtonStyle.danger, label='Non')
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      self.request_spiredetails_data.last_interaction = interaction
      match self.whichone:
        case 'hero_bonus':
          await self.outer.build_hero_bonus_modal(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)
        case 'monster_bonus':
          await self.outer.build_monster_bonus_modal(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)         

    @discord.ui.button(style=discord.ButtonStyle.success, label='Oui')
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      self.request_spiredetails_data.last_interaction = interaction
      await self.outer.build_initial_view(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)

    async def on_timeout(self):
      if self.request_spiredetails_data.handle_timeout:
        self.outer.logger.log_only('debug', 'yes/no view timeout')
        await self.outer.interaction_handler.send_timeout_message(interaction=self.request_spiredetails_data.last_interaction, timeout=self.timeout)
  
  class MonsterBonusModal(discord.ui.Modal):
##### MODALE DE SAISIE DES BONUS DE MONSTRES
    def __init__(self, outer, request_spiredetails_data):
      outer.logger.log_only('debug', 'init monster bonus modal')
      super().__init__(title='Bonus des monstres', timeout=180)
      self.outer = outer
      self.request_spiredetails_data = request_spiredetails_data
     
      self.monster_bonus_type_field = self.create_text_input(label='All [XXX] gain [YYY]', key='type', default='Entrez ici ce qui correspond à XXX')
      self.monster_bonus_buff_field = self.create_text_input(label='All [XXX] gain [YYY]', key='buff', default='Entrez ici ce qui correspond à YYY')

    async def on_submit(self, interaction: discord.Interaction):
      self.stop()
      self.outer.logger.log_only('debug', 'modal submit')
      if 'monster_bonus' not in self.request_spiredetails_data.selected_details:
        self.request_spiredetails_data.selected_details['monster_bonus'] = {}
      if self.monster_bonus_type_field.value != 'Entrez ici ce qui correspond à XXX':
        print(self.monster_bonus_type_field.value)
        self.request_spiredetails_data.selected_details['monster_bonus']['type'] = self.monster_bonus_type_field.value
      if self.monster_bonus_buff_field.value != 'Entrez ici ce qui correspond à YYY':
        print(self.monster_bonus_buff_field.value)
        self.request_spiredetails_data.selected_details['monster_bonus']['buff'] = self.monster_bonus_buff_field.value
      await self.outer.build_monster_bonus_validation_view(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)

    def create_text_input(self, label, key, default):
      monster_bonus = self.request_spiredetails_data.selected_details.get('monster_bonus', {})
      value = monster_bonus.get(key, default)
      text_input = discord.ui.TextInput(label=label, placeholder=value, required=False)
      self.add_item(text_input)
      return text_input
    
    async def on_timeout(self):
      if self.request_spiredetails_data.handle_timeout:
        self.stop()
        self.outer.logger.log_only('debug', 'monster bonus modal timeout')
        await self.outer.interaction_handler.send_timeout_message(interaction=self.request_spiredetails_data.last_interaction, timeout=self.timeout)


  class BracketView(discord.ui.View):
##### VIEW DE CHOIX DU BRACKET POUR LES TALENTS
    def __init__(self, outer, request_spiredetails_data):
      outer.logger.log_only('debug', 'init bracket view')
      super().__init__(timeout=180)
      self.outer = outer
      self.request_spiredetails_data = request_spiredetails_data

      self.tier_selector.options = []
      for t in self.outer.tiers:
        if self.request_spiredetails_data.selected_details.get('talents').get(t):
          emoji = '🟢'
        else:
          emoji = '🔴'
        self.tier_selector.options.append(discord.SelectOption(label=t, value=t, emoji=emoji))
      self.tier_selector.placeholder = 'Choix du tier'

    @discord.ui.select(row=0, cls=discord.ui.Select) 
    async def tier_selector(self, interaction: discord.Interaction, select: discord.ui.Select):
      self.tier_selector.placeholder = self.tier_selector.values[0]
      await interaction.response.defer()

    @discord.ui.button(row=1, style=discord.ButtonStyle.danger, label='Annuler')
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      self.request_spiredetails_data.last_interaction = interaction
      await self.outer.build_initial_view(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)

    @discord.ui.button(row=1, style=discord.ButtonStyle.success, label='Suivant')
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      print('tier validé')
      self.request_spiredetails_data.last_interaction = interaction
      if not self.request_spiredetails_data.selected_details.get('talents').get(self.tier_selector.values[0]):
        print('here')
        self.request_spiredetails_data.selected_details['talents'][self.tier_selector.values[0]] = [''] * 13
        print(self.request_spiredetails_data.selected_details['talents'][self.tier_selector.values[0]])
      self.request_spiredetails_data.selected_tier = self.tier_selector.values[0]
      print('pouet')
      await self.outer.build_talents_modal(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)

    async def on_timeout(self):
      if self.request_spiredetails_data.handle_timeout:
        self.outer.logger.log_only('debug', 'bracket view timeout')
        await self.outer.interaction_handler.send_timeout_message(interaction=self.request_spiredetails_data.last_interaction, timeout=self.timeout)

  class TalentsModal(discord.ui.Modal):
##### MODALE DE SAISIE DES BONUS DE MONSTRES
    def __init__(self, outer, request_spiredetails_data, step):
      outer.logger.log_only('debug', f'init talents modal ({step}/3)')
      super().__init__(title=f'Talents en {request_spiredetails_data.selected_tier} ({step}/3)', timeout=180)
      self.outer = outer
      self.request_spiredetails_data = request_spiredetails_data
      self.step = step

      start_index = (step - 1) * 5
      end_index = min(start_index + 5, self.outer.max_talents_floor)
      for i in range(start_index, end_index):
        value = self.request_spiredetails_data.selected_details.get('talents').get(self.request_spiredetails_data.selected_tier)[i]
        default = str(value) if value else ''
        text_input = discord.ui.TextInput(label=f'Floor {i+1}', custom_id=f'Floor_{i+1}', default=default, required=True, style=discord.TextStyle.short)
        self.add_item(text_input)

    async def on_submit(self, interaction: discord.Interaction):
      self.stop()
      self.outer.logger.log_only('debug', f'talent modal {self.step} submit')
      for child in self.children:
        idx = int(child.custom_id.split('_')[1]) -1
        self.request_spiredetails_data.selected_details.get('talents').get(self.request_spiredetails_data.selected_tier)[idx] = child.value
      await self.outer.build_between_and_after_talents_modals_view(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction, step=self.step)
    
    async def on_timeout(self):
      if self.request_spiredetails_data.handle_timeout:
        self.stop()
        self.outer.logger.log_only('debug', f'talents modal ({self.step}/3) timeout')
        await self.outer.interaction_handler.send_timeout_message(interaction=self.request_spiredetails_data.last_interaction, timeout=self.timeout)

  class BetweenAndAfterTalentsModalsView(discord.ui.View):
##### VIEW ENTRE 2 MODALES POUR CONTOURNER L'API DISCORD QUI REFUSE LES MODALES SUCCESSIVES OU VALIDATION FINALE
    def __init__(self, outer, request_spiredetails_data, step):
      outer.logger.log_only('debug', f'init between and after talents view ({step}/3)')
      super().__init__(timeout=180)
      self.outer = outer
      self.request_spiredetails_data = request_spiredetails_data
      self.step = step
      self.continue_button.label = 'Continuer' if self.step < 3 else 'Valider'

    @discord.ui.button(style=discord.ButtonStyle.danger, label='Modifier')
    async def change_button(self, interaction: discord.Interaction, button: discord.ui.Button):
      if self.step == 3:
        self.step = 1
      await self.outer.build_talents_modal(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction, step=self.step)

    @discord.ui.button(style=discord.ButtonStyle.success, label='Continuer')
    async def continue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
      if self.step < 3:
        await self.outer.build_talents_modal(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction, step=self.step + 1)
      else:
        await self.outer.build_initial_view(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)

    async def on_timeout(self):
      if self.request_spiredetails_data.handle_timeout:
        self.stop()
        self.outer.logger.log_only('debug', f'between and after talents view ({self.step}/3) timeout')
        await self.outer.interaction_handler.send_timeout_message(interaction=self.request_spiredetails_data.last_interaction, timeout=self.timeout)

  class FinalView(discord.ui.View):
##### VIEW DE VALIDATION FINALE
    def __init__(self, outer, request_spiredetails_data):
      outer.logger.log_only('debug', f'init final view')
      super().__init__(timeout=180)
      self.outer = outer
      self.request_spiredetails_data = request_spiredetails_data

    @discord.ui.button(style=discord.ButtonStyle.danger, label='Modifier')
    async def change_button(self, interaction: discord.Interaction, button: discord.ui.Button):
      await self.outer.build_initial_view(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)

    @discord.ui.button(style=discord.ButtonStyle.success, label='Valider')
    async def validate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.outer.build_final_response(request_spiredetails_data=self.request_spiredetails_data, interaction=interaction)

    async def on_timeout(self):
      if self.request_spiredetails_data.handle_timeout:
        self.stop()
        self.outer.logger.log_only('debug', f'final view timeout')
        await self.outer.interaction_handler.send_timeout_message(interaction=self.request_spiredetails_data.last_interaction, timeout=self.timeout)

##### COMMANDE
  @app_commands.command(name='spiredetails')
  async def spiredetails_app_command(self, interaction: discord.Interaction):
    self.logger.command_log('spiredetails', interaction)
    self.interaction_handler = InteractionHandler(self.bot)
    await self.interaction_handler.send_wait_message(interaction=interaction)
    await self.get_response(interaction=interaction)
  
  async def get_response(self, interaction: discord.Interaction = None):
    request_spiredetails_data = self.CommandData()
    request_spiredetails_data.last_interaction = interaction
    request_spiredetails_data.handle_timeout = True
    request_spiredetails_data.spire = await self.bot.back_requests.call("getSpireByDate", False, [{'date': datetime.now(tz=timezone.utc).isoformat()}])
    ###for tests
    if request_spiredetails_data.spire:
      request_spiredetails_data.climb = self.bot.spire_service.get_current_climb(request_spiredetails_data.spire)
      climb_data = next((c for c in request_spiredetails_data.spire.get('climbs') if c.get('number') == request_spiredetails_data.climb), None)
      if climb_data.get('climb_details') != {}:
        request_spiredetails_data.selected_details = climb_data.get('climb_details')
        if 'map' in request_spiredetails_data.selected_details.keys():
          request_spiredetails_data.selected_details['map'] = next((map for map in self.maps if request_spiredetails_data.selected_details.get('map').get('name') == map.get('name')), None)
          request_spiredetails_data.selected_details['map']['water_or_lava'] = climb_data.get('climb_details').get('map').get('water_or_lava')
      else:
        request_spiredetails_data.selected_details = {'map': None, 'hero_bonus': {}, 'monster_bonus': {}, 'talents': {}}
    else :
      request_spiredetails_data.climb = 4
    ###
    await self.build_initial_view(request_spiredetails_data=request_spiredetails_data, interaction=interaction)
    
  async def build_initial_view(self, request_spiredetails_data, interaction: discord.Interaction = None):
    view = self.InitialView(outer=self, request_spiredetails_data=request_spiredetails_data)
    content = f'# Détails du climb {request_spiredetails_data.climb} #\nVeuillez choisir quel détail ajouter/modifier ou valider'
    await self.interaction_handler.send_view(interaction=interaction, content=content, view=view)

  async def build_map_view(self, request_spiredetails_data, interaction: discord.Interaction = None):
    view = self.MapView(outer=self, request_spiredetails_data=request_spiredetails_data)
    content = f'# Map du climb {request_spiredetails_data.climb} #\nVeuillez choisir ou confirmer la map déjà renseignée'
    if request_spiredetails_data.selected_details.get('map'):
      print('map!')
      file = self.bot.map_service.generate_map(request_spiredetails_data.selected_details.get('map'))
      await self.interaction_handler.send_view_with_file(interaction=interaction, content=content, view=view, file=file)
    else:  
      print('pas map!')
      await self.interaction_handler.send_view(interaction=interaction, content=content, view=view)

  async def build_water_or_lava_view(self, request_spiredetails_data, interaction: discord.Interaction = None):
    view = self.WaterOrLavaView(outer=self, request_spiredetails_data=request_spiredetails_data)
    content = f'# Map du climb {request_spiredetails_data.climb} #\nSur cette map, s\'agit-il d\'eau ou de lave ?'
    request_spiredetails_data.selected_map_pic = self.bot.map_service.generate_map(map=request_spiredetails_data.selected_details.get('map'))
    await self.interaction_handler.send_view_with_file(interaction=interaction, content=content, view=view, file=request_spiredetails_data.selected_map_pic)

  async def build_hero_bonus_modal(self, request_spiredetails_data, interaction: discord.Interaction = None):
    request_spiredetails_data.last_interaction = interaction
    modal = self.HeroBonusModal(outer=self, request_spiredetails_data=request_spiredetails_data)
    await self.interaction_handler.send_modal(interaction=interaction, modal=modal)

  async def build_hero_bonus_validation_view(self, request_spiredetails_data, interaction: discord.Interaction = None):
    request_spiredetails_data.last_interaction = interaction
    view = self.YesNoView(outer=self, request_spiredetails_data=request_spiredetails_data, whichone='hero_bonus')
    request_content = ''
    if request_spiredetails_data.selected_details.get('hero_bonus').get('type', None):
      request_content = f'+250 score for each {request_spiredetails_data.selected_details.get('hero_bonus').get('type')} in team\n'
    if request_spiredetails_data.selected_details.get('hero_bonus').get('buff', None):
      request_content += f'All {request_spiredetails_data.selected_details.get('hero_bonus').get('type')} gain {request_spiredetails_data.selected_details.get('hero_bonus').get('buff')}\n'
    if request_content == '':
      request_content = 'Aucun bonus :shrug:\n'
    content = f'# Bonus de héros du climb {request_spiredetails_data.climb} #\n{request_content}'
    await self.interaction_handler.send_view(interaction=interaction, content=content, view=view)

  async def build_monster_bonus_modal(self, request_spiredetails_data, interaction: discord.Interaction = None):
    request_spiredetails_data.last_interaction = interaction
    modal = self.MonsterBonusModal(outer=self, request_spiredetails_data=request_spiredetails_data)
    await self.interaction_handler.send_modal(interaction=interaction, modal=modal)

  async def build_monster_bonus_validation_view(self, request_spiredetails_data, interaction: discord.Interaction = None):
    request_spiredetails_data.last_interaction = interaction
    view = self.YesNoView(outer=self, request_spiredetails_data=request_spiredetails_data, whichone='monster_bonus')
    request_content = ''
    if request_spiredetails_data.selected_details.get('monster_bonus').get('type', None) and request_spiredetails_data.selected_details.get('monster_bonus').get('buff', None):
      request_content += f'All {request_spiredetails_data.selected_details.get('monster_bonus').get('type')} gain {request_spiredetails_data.selected_details.get('monster_bonus').get('buff')}\n'
    if request_content == '':
      request_content = 'Aucun bonus :shrug:\n'
    content = f'# Bonus des monstres du climb {request_spiredetails_data.climb} #\n{request_content}'
    await self.interaction_handler.send_view(interaction=interaction, content=content, view=view)

  async def build_bracket_view(self, request_spiredetails_data, interaction: discord.Interaction = None):
    request_spiredetails_data.last_interaction = interaction
    view = self.BracketView(outer=self, request_spiredetails_data=request_spiredetails_data)
    content = f'# Choix du tier pour le climb {request_spiredetails_data.climb} #\nVeuillez choisir pour quel climb ajouter les talents'
    await self.interaction_handler.send_view(interaction=interaction, content=content, view=view)

  async def build_talents_modal(self, request_spiredetails_data, interaction: discord.Interaction = None, step = 1):
    request_spiredetails_data.last_interaction = interaction
    modal = self.TalentsModal(outer=self, request_spiredetails_data=request_spiredetails_data, step=step)
    await self.interaction_handler.send_modal(interaction=interaction, modal=modal)

  async def build_between_and_after_talents_modals_view(self, request_spiredetails_data, step, interaction: discord.Interaction = None):
    request_spiredetails_data.last_interaction = interaction
    if step < 3:
      content = f'# Talents {step}/3 enregistrés #\n'
    else:
      content = f'# Talents en {request_spiredetails_data.selected_tier} #\n'
    max_range = (step - 1) * 5 + 5
    max_range = self.max_talents_floor if max_range > self.max_talents_floor else max_range
    for i in range(max_range):
      content += f'{i+1}. {request_spiredetails_data.selected_details.get('talents').get(request_spiredetails_data.selected_tier)[i]}\n'
    view = self.BetweenAndAfterTalentsModalsView(outer=self, request_spiredetails_data=request_spiredetails_data, step=step)
    await self.interaction_handler.send_view(interaction=interaction, content=content, view=view)

  async def build_final_view(self, request_spiredetails_data, interaction: discord.Interaction = None):
    print('here')
    request_spiredetails_data.last_interaction = interaction
    self.embed_response = await self.build_final_embed_response(request_spiredetails_data)
    print(self.embed_response)
    view = self.FinalView(outer=self, request_spiredetails_data=request_spiredetails_data)
    print(view)
    if request_spiredetails_data.selected_details.get('map'):
      file = self.bot.map_service.generate_map(map=request_spiredetails_data.selected_details.get('map'))
      print('final view & embed & file ok')
      await self.interaction_handler.send_view_and_embed_with_file(interaction=interaction, response=self.embed_response, view=view, file=file)
    else:
      print('final view & embed ok')
      await self.interaction_handler.send_view_and_embed(interaction=interaction, response=self.embed_response, view=view)

  async def build_final_response(self, request_spiredetails_data, interaction: discord.Interaction = None):
    request_spiredetails_data.last_interaction = interaction
    request_spiredetails_data.handle_timeout = False
    if request_spiredetails_data.selected_details.get('map'):
      file = self.bot.map_service.generate_map(map=request_spiredetails_data.selected_details.get('map'))
      message = await self.interaction_handler.send_embed_with_file(interaction=interaction, response=self.embed_response, file=file)
    else:
      message = await self.interaction_handler.send_embed(interaction=interaction, response=self.embed_response)
    await self.send_spiredetails_update(request_spiredetails_data=request_spiredetails_data)
    await self.handle_spire(request_spiredetails_data=request_spiredetails_data, message=message)

  async def build_final_embed_response(self, request_spiredetails_data):
    description = f'# Détails du climb {request_spiredetails_data.climb} #\n'
    
    if request_spiredetails_data.selected_details.get('hero_bonus'):
      description += '### Bonus des héros ###\n'
      if request_spiredetails_data.selected_details.get('hero_bonus').get('type'):
        description += f'+250 score for each {request_spiredetails_data.selected_details.get('hero_bonus').get('type')} in team\n'
      if request_spiredetails_data.selected_details.get('hero_bonus').get('buff'):
        description += f'All {request_spiredetails_data.selected_details.get('hero_bonus').get('type')} gain {request_spiredetails_data.selected_details.get('hero_bonus').get('buff')}\n'
    
    if request_spiredetails_data.selected_details.get('monster_bonus').get('type') and request_spiredetails_data.selected_details.get('monster_bonus').get('buff'):
      description += f'### Bonus des monstres ###\nAll {request_spiredetails_data.selected_details.get('monster_bonus').get('type')} gain {request_spiredetails_data.selected_details.get('monster_bonus').get('buff')}\n'
    
    tier_known_talents = [{'index': i, 'tier': t} for i, t in enumerate(self.tiers) if t in request_spiredetails_data.selected_details.get('talents').keys()]
    tier_known_talents = sorted(tier_known_talents, key=lambda x:x.get('index'))
    tier_known_talents = [t.get('tier') for t in tier_known_talents]
    print(tier_known_talents)
    if len(tier_known_talents) > 0:
      for tier in tier_known_talents:
        print(request_spiredetails_data.selected_details.get('talents').get(tier))
        description += f'### Talents en {tier} ###\n'
        description += ''.join([f'{i+1}. {talent}\n' for i, talent in enumerate(request_spiredetails_data.selected_details.get('talents').get(tier))])
        description += '\n'

    return {'title': '', 'description': description, 'color': 'blue'}
  
  async def send_spiredetails_update(self, request_spiredetails_data):
    climb_details = copy.deepcopy(request_spiredetails_data.selected_details)
    climb_details['map'] = {'name': request_spiredetails_data.selected_details.get('map').get('name'), 'water_or_lava': request_spiredetails_data.selected_details.get('map').get('water_or_lava')}
    await self.bot.back_requests.call('addClimbDetails', False, [{'date': datetime.now(tz=timezone.utc).isoformat(), 'climb_details': climb_details}])
  
  async def handle_spire(self, request_spiredetails_data, message):
    print(f'request_details: {request_spiredetails_data.selected_details}')
    date = datetime.now(tz=timezone.utc).isoformat()
    print(f'date: {date}')
    self.embed_response = message.embeds[0]
    print(self.embed_response)
    print(request_spiredetails_data.spire.get('channels'))
    print(message.channel.id)
    spire_channel = next((c for c in request_spiredetails_data.spire.get('channels') if c.get('discord_channel_id') == message.channel.id), None)
    print(spire_channel)
    if spire_channel is None:
      await self.bot.back_requests.call('addChannelToSpire', False, [{'date': date, 'channel_id': message.channel.id}])
    for channel_data in request_spiredetails_data.spire.get('channels'):
      print(channel_data)
      if channel_data.get('climb_details_message_id'):
        print('channel avec message déjà renseigné -> unpin & delete')
        channel = self.bot.get_channel(channel_data.get('discord_channel_id'))
        old_message = await channel.fetch_message(channel_data.get('climb_details_message_id'))
        if old_message and old_message.pinned:
          await old_message.unpin()
          await old_message.delete()
          print(f'{old_message.id} unpinned and deleted ok')
      
      if channel_data != spire_channel:
        print('autre channel -> post & pin')
        channel = self.bot.get_channel(channel_data.get('discord_channel_id'))
        if request_spiredetails_data.selected_details.get('map'):
          print('embed & file')
          print(f'map: {request_spiredetails_data.selected_details.get('map')}')
          file = self.bot.map_service.generate_map(map=request_spiredetails_data.selected_details.get('map'))
          print(f'file {file.filename} ok')
          new_message = await channel.send(embed=self.embed_response, file=file)
        else:
          print('embed tout court')
          new_message = await channel.send(embed=self.embed_response)
      else:
        print('même channel -> pin')
        new_message = message
      pinned = await self.bot.back_requests.call('addMessageId', False, [{'date': date, 'channel_id': new_message.channel.id, 'climb_details_message_id': new_message.id}])
      if pinned:
        await new_message.pin()
        print(f'{new_message.id} pinned')


  async def setup_with_bot(self, bot, param_list=None):
    try:
      if param_list is None:
        maps = bot.map_service.maps
        self.maps = [m for m in maps if m.get('gameplay') == 'spire']
      else:
        self.maps = param_list
      spire_configs = await bot.back_requests.call('getMapBonuses', False)
      if spire_configs:
        self.hero_bonus_choices = spire_configs.get('hero_bonus_types')
        self.monster_bonus_choices = spire_configs.get('monster_bonus_types')
        self.buff_choices = spire_configs.get('buffs')
      else:
        self.logger.log_only('warning', f'couldn\'t get spireDetails config: {e}')
    except Exception as e:
      self.logger.log_only('warning', f'spiredetails setup error: {e}')

async def setup(bot):
  await bot.add_cog(Spiredetails(bot))