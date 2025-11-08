import typing
import discord
import emoji
import re

from discord.ext import commands
from discord import app_commands
from discord.ui import Button, TextInput

from service.command import CommandService
from service.interaction_handler import InteractionHandler
from utils.str_utils import str_to_slug, str_to_int, int_to_str


class Reward(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.interaction_handler = None
    self.reward_command = next((c for c in bot.static_data.commands if c['name'] == 'reward'), None)
    
    CommandService.init_command(self.reward_app_command, self.reward_command)
    self.levels = None
    self.levelname_choices = None

  class CommandData():
    def __init__(self):
      self.current_level = None
      self.current_reward_choice = None
      self.selected_reward = None
      self.view = None
      self.modal = None
      self.times = None
      self.last_interaction = None
      self.handle_timeout = False

  class ButtonChoiceView(discord.ui.View):
###### VUES DES CHOIX AVEC BOUTONS
    def __init__(self, outer, selectable_choices, request_reward_data):
      super().__init__(timeout=180)
      outer.logger.log_only('debug', 'init button choice view')
      self.outer = outer
      self.selectable_choices = selectable_choices
      self.request_reward_data = request_reward_data

      if self.request_reward_data.current_reward_choice == 'type': ## Choix entre dust et gear -> on mix quality et type pour créer des boutons
        print('quality & type choice')
        for i in range(len(self.selectable_choices)):
          type_choice = self.selectable_choices[i]
          quality_choices = type_choice['choices'][0]
          for j in range(len(quality_choices['choices'])):
            quality_choice = quality_choices['choices'][j]
            choice_button = discord.ui.Button(
              label=f'{quality_choice.get('name')} {type_choice.get('name')}',
              style=discord.ButtonStyle.blurple if type_choice.get('name') in self.selectable_choices else discord.ButtonStyle.grey,
              custom_id=str_to_slug(f'{quality_choice.get('name')} {type_choice.get('name')}')
            )
            choice_button.emoji = self.get_emoji_from_icon(quality_choice.get('icon'))
            choice_button.callback = self.create_choice_callback(choice_button=choice_button, type='double')
            self.add_item(choice_button)
      else: ## Choix gear uniquement -> on propose directement la quality
        print('quality choice')
        for choice in self.selectable_choices:       
          choice_button = discord.ui.Button(
            label=choice.get('name'),
            style=discord.ButtonStyle.blurple if choice.get('name') in self.selectable_choices else discord.ButtonStyle.grey,
            custom_id=str_to_slug(choice.get('name'))
          )
          if self.request_reward_data.current_reward_choice != 'type':
            choice_button.emoji = self.get_emoji_from_icon(choice.get('icon'))
          choice_button.callback = self.create_choice_callback(choice_button=choice_button, type='single')
          self.add_item(choice_button)
      self.add_validation_button()

    def create_choice_callback(self, choice_button: discord.ui.Button, type: str):
      async def callback(interaction: discord.Interaction):
        self.request_reward_data.last_interaction = interaction
        choice_button.style = discord.ButtonStyle.grey if choice_button.style == discord.ButtonStyle.blurple else discord.ButtonStyle.blurple
        print('button check')
        if choice_button.style == discord.ButtonStyle.blurple:
          if type == 'double':
            print('here')
            self.request_reward_data.selected_reward['type'] = choice_button.label.split(' ')[1]
            self.request_reward_data.selected_reward['quality'] = choice_button.label.split(' ')[0]
            print('there')
            print(f'type : {self.request_reward_data.selected_reward['type']}')
            print(f'quality : {self.request_reward_data.selected_reward['quality']}')
          else:
            self.request_reward_data.selected_reward[self.request_reward_data.current_reward_choice] = choice_button.label
          await self.unselect_all_others(choice_button.custom_id)
        else:
          if self.request_reward_data.current_reward_choice in self.request_reward_data.selected_reward.keys():
            if type == 'double':
              del self.request_reward_data.selected_reward['type']
              del self.request_reward_data.selected_reward['quality']
            else:
              del self.request_reward_data.selected_reward[self.request_reward_data.current_reward_choice]
        await self.update_validation_button_state(interaction=interaction)
      return callback
    
    async def update_validation_button_state(self, interaction: discord.Interaction):
      print('update validation button state')
      validation_button = discord.utils.get(self.children, custom_id='submit' if self.are_all_choices_done() else 'next')
      if validation_button:
        print('validation_button found')
        validation_button.disabled = not self.has_one_selected()
        await self.outer.interaction_handler.send_view(interaction=interaction, view=self)

    def add_validation_button(self):
      validation_button = discord.ui.Button(
        style=discord.ButtonStyle.green,
        disabled=not self.has_one_selected()
      )
      if self.are_all_choices_done():
        validation_button.label = "Valider"
        validation_button.custom_id = "submit"
        validation_button.callback = self.submit_callback
      else:
        validation_button.label = "Suivant"
        validation_button.custom_id = "next"
        validation_button.callback = self.next_callback
      self.add_item(validation_button)
    
    async def submit_callback(self, interaction: discord.Interaction):
      self.request_reward_data.last_interaction = interaction
      self.request_reward_data.view.stop()
      await self.outer.build_validation_view(interaction=interaction, request_reward_data=self.request_reward_data)

    async def next_callback(self, interaction: discord.Interaction):
      self.request_reward_data.last_interaction = interaction
      self.request_reward_data.view.stop()
      next_view_choices = self.select_next_view()
      if next_view_choices:
        print('next view')
        print(next_view_choices)
        next_choices_content = f'\n### Choix {self.request_reward_data.current_reward_choice} pour le type de reward {self.request_reward_data.selected_reward.get('type')} : ###'
        print(next_choices_content)
        self.request_reward_data.view = self.outer.SelectorChoiceView(outer=self.outer, selectable_choices=next_view_choices, request_reward_data=self.request_reward_data, current_choices_list_begin=0)
        await self.outer.interaction_handler.send_view(interaction=interaction, content=next_choices_content, view=self.request_reward_data.view)
        return
      await self.outer.build_quantity_modal(interaction=interaction, request_reward_data=self.request_reward_data)

    def select_next_view(self):
      print('select next view')
      current_reward = next((c for c in self.request_reward_data.current_level.get('reward_choices') if c.get('name') == self.request_reward_data.selected_reward.get('type')), None)
      if self.request_reward_data.selected_reward['type'] == 'gear':
        print('quality & gear ok')
        self.request_reward_data.current_reward_choice = 'item'
        return sorted(current_reward.get('choices')[1].get('choices'), key=lambda x:x['grade']) 
      else:
        return False
    
    def get_emoji_from_icon(self, icon):
      if 'customIcon' in icon or icon == '':
        return None
      unicode_match = re.match(r'\\U([0-9a-fA-F]{8})', icon)
      if unicode_match:
        return chr(int(unicode_match.group(1), 16))
      return emoji.emojize(icon)
    
    async def unselect_all_others(self, selected_id):
      for button in self.request_reward_data.view.children:
        if isinstance(button, discord.ui.Button):
          if button.custom_id not in [selected_id, 'submit', 'next']:
            button.style = discord.ButtonStyle.grey
    
    def has_one_selected(self) -> bool:
      for button in self.children:
        if isinstance(button, discord.ui.Button):
          if button.custom_id not in ['submit', 'next'] and button.style == discord.ButtonStyle.blurple:
            return True
      return False
    
    def are_all_choices_done(self) -> bool:
      if not 'type' in self.request_reward_data.selected_reward.keys():
        return False # rien n'est encore saisi -> False
      selected_choice = next((c for c in self.request_reward_data.current_level.get('reward_choices') if c.get('name') == self.request_reward_data.selected_reward.get('type')), None)
      if selected_choice.get('has_quantity'):
        return False # il y a encore des quantités à saisir -> False
      last_choice = selected_choice.get('choices')[len(selected_choice.get('choices')) - 1]
      if self.request_reward_data.current_reward_choice != last_choice.get('name').lower():
        return False # il y a encore des choix à faire -> False
      return True
    
    async def on_timeout(self):
      if self.request_reward_data.handle_timeout:
        self.outer.logger.log_only('debug', 'choice view timeout')
        await self.outer.interaction_handler.send_timeout_message(interaction=self.request_reward_data.last_interaction, timeout=self.timeout)      


  class SelectorChoiceView(discord.ui.View):
###### VUES DES CHOIX AVEC SELECTEUR
    def __init__(self, outer, selectable_choices: list, request_reward_data, current_choices_list_begin: int):
      super().__init__(timeout=180)
      outer.logger.log_only('debug', 'init selector choice view')
      self.outer = outer
      self.selectable_choices = selectable_choices
      self.request_reward_data = request_reward_data
      self.current_choices_list_begin = current_choices_list_begin
      choices_end = len(self.selectable_choices) if self.current_choices_list_begin + 24 > len(self.selectable_choices) else self.current_choices_list_begin + 24
      for i in range(self.current_choices_list_begin, choices_end):
        print(i)
        self.choice_selector.options.append(discord.SelectOption(label=self.selectable_choices[i].get('name'), value=self.selectable_choices[i].get('name')))
      print(f'Choice list : {self.choice_selector.options}')
      print(f'len : {len(self.choice_selector.options)}')
      self.choice_selector.placeholder = 'Choisissez un item'
      previous_disabled = False
      next_disabled = False
      if len(self.selectable_choices) > 25:
        print('build buttons')
        if self.current_choices_list_begin == 0:
          previous_disabled = True
          print('previous disabled')
        if self.current_choices_list_begin + 24 > len(self.selectable_choices):
          next_disabled = True
          print('next disabled')
        print('add previous')
        self.add_list_button(label='Previous', is_disabled=previous_disabled)
        print('add next')
        self.add_list_button(label='Next', is_disabled=next_disabled)
    
    @discord.ui.select(cls=discord.ui.Select) 
    async def choice_selector(self, interaction: discord.Interaction, select: discord.ui.Select):
      self.request_reward_data.last_interaction = interaction
      self.request_reward_data.selected_reward['item'] = self.choice_selector.values[0]
      await self.outer.build_validation_view(interaction=interaction, request_reward_data=self.request_reward_data)

    def add_list_button(self, label: str, is_disabled: bool):
      print(f'build {label} button')
      button = discord.ui.Button(
        label=label,
        custom_id=label,
        style=discord.ButtonStyle.grey if is_disabled else discord.ButtonStyle.blurple,
        disabled=is_disabled
      )
      button.callback = self.previous_callback if label == 'Previous' else self.next_callback
      self.add_item(button)

    async def next_callback(self, interaction: discord.Interaction):
      self.request_reward_data.view = self.outer.SelectorChoiceView(outer=self.outer, selectable_choices=self.selectable_choices, request_reward_data= self.request_reward_data, current_choices_list_begin=self.current_choices_list_begin + 25)
      await self.outer.interaction_handler.send_view(interaction=interaction, view=self.request_reward_data.view)
    
    async def previous_callback(self, interaction: discord.Interaction):
      self.request_reward_data.view = self.outer.SelectorChoiceView(outer=self.outer, selectable_choices=self.selectable_choices, request_reward_data= self.request_reward_data, current_choices_list_begin=self.current_choices_list_begin - 25)
      await self.outer.interaction_handler.send_view(interaction=interaction, view=self.request_reward_data.view)   


  class InputModal(discord.ui.Modal):
##### MODALE DE QUANTITÉ
    def __init__(self, outer, title:str, request_reward_data):
      super().__init__(title=title, timeout=180)
      outer.logger.log_only('debug', 'init quantity modal')
      self.outer = outer
      self.request_reward_data = request_reward_data
      self.input_quantity = discord.ui.TextInput(label='Entrez une quantité', custom_id='input', required=True)
      self.add_item(self.input_quantity)

    async def on_submit(self, interaction: discord.Interaction):
      self.stop()
      self.request_reward_data.last_interaction = interaction
      if self.check_quantity():
        response = {'title': 'Erreur', 'description': f"{self.input_quantity.value} n'est pas une quantité valide, merci de recommencer :rolling_eyes:", 'color': 'red'}
        self.request_reward_data.handle_timeout = False
        await self.outer.interaction_handler.send_embed(interaction=interaction, response=response)
        self.logger.ok_log('reward')
        return
      await self.outer.build_validation_view(interaction=interaction, request_reward_data=self.request_reward_data)

    def check_quantity(self) -> bool:
      quantity = str_to_int(self.input_quantity.value)
      wrong_entry = False
      if quantity is None:
        wrong_entry = True
      if isinstance(quantity, int):
        if quantity <= 0:
          wrong_entry = True
      if not wrong_entry:
        self.request_reward_data.selected_reward['quantity'] = quantity
      return wrong_entry

    async def on_timeout(self):
      if self.request_reward_data.handle_timeout:
        self.outer.logger.log_only('debug', 'input modal timeout')
        self.stop()
        await self.outer.interaction_handler.send_timeout_message(interaction=self.request_reward_data.last_interaction, timeout=self.timeout)

  class ValidationView(discord.ui.View):
##### VUE FINALE DE VALIDATION DE LA REWARD
    def __init__(self, outer, request_reward_data):
      super().__init__(timeout=180)
      outer.logger.log_only('debug', 'init validation view')
      self.outer = outer
      self.request_reward_data = request_reward_data
      outer.logger.log_only('debug', f'times value: {self.request_reward_data.times}')
      self.many_times_selector.options = [discord.SelectOption(label=str(i), value=i) for i in range(1,6)]
      self.many_times_selector.placeholder = str(self.request_reward_data.times)
      outer.logger.log_only('debug', 'Selector initialized')

    @discord.ui.select(cls=discord.ui.Select) 
    async def many_times_selector(self, interaction: discord.Interaction, select: discord.ui.Select):
      self.request_reward_data.last_interaction = interaction
      self.request_reward_data.times = self.many_times_selector.values[0]
      await self.outer.build_validation_view(interaction=interaction, request_reward_data=self.request_reward_data)

    @discord.ui.button(label='Annuler', style=discord.ButtonStyle.red)
    async def cancel_reward(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      self.request_reward_data.handle_timeout = False
      description = f'# {self.request_reward_data.current_level.get('name')} # \nRécompense annulée :)'
      response = {'title': '', 'description': description, 'color': 'red'}
      await self.outer.interaction_handler.send_embed(interaction=interaction, response=response)
      self.outer.logger.ok_log('reward')
    
    @discord.ui.button(label='Valider', style=discord.ButtonStyle.green)
    async def submit_reward(self, interaction: discord.Interaction, button: discord.ui.Button):
      self.stop()
      self.request_reward_data.handle_timeout = False
      self.request_reward_data.selected_reward['times'] = int(self.request_reward_data.times)
      response = await self.outer.bot.level_service.add_reward(emojis=interaction.guild.emojis, level_name=self.request_reward_data.current_level.get('name'), reward_data=self.request_reward_data.selected_reward)
      await self.outer.interaction_handler.send_embed(interaction=interaction, response=response)
      await self.outer.setup()
      self.outer.logger.ok_log('reward')
    
    async def on_timeout(self):
      if self.request_reward_data.handle_timeout:
        self.outer.logger.log_only('debug', 'validation view timeout')
        await self.outer.interaction_handler.send_timeout_message(interaction=self.request_reward_data.last_interaction, timeout=self.timeout)


  ##### COMMANDE
  async def level_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await CommandService.return_autocompletion(self.levelname_choices, current)

  @app_commands.autocomplete(level=level_autocomplete)
  @app_commands.command(name='reward')
  async def reward_app_command(self, interaction: discord.Interaction, level: str):
    self.interaction_handler = InteractionHandler(self.bot)
    self.logger.command_log('reward', interaction)
    self.logger.log_only('debug', f"level : {level}")
    await self.get_response(interaction, level)

  async def get_response(self, interaction, level_name):
    request_reward_data = self.CommandData()
    request_reward_data.times = 1
    request_reward_data.last_interaction = interaction
    request_reward_data.handle_timeout = True
    if level_name not in [cl.name for cl in self.levelname_choices]:
      self.logger.log_only('debug', 'level inexistant')
      response = {'title': 'Erreur', 'description': f'Le level {level_name} n\'existe pas.\nMerci de vérifier et/ou de contacter Spirou ou Prep pour la création du level si besoin :wink:', 'color': 'red'}
      await self.interaction_handler.send_embed(interaction=interaction, response=response)
      self.logger.ok_log('reward')
      return
    request_reward_data.current_level = next((l for l in self.levels if str_to_slug(level_name) == l.get('name_slug')), None)
    await self.build_initial_view(interaction=interaction, request_reward_data=request_reward_data)

  async def initial_view_with_multiple_choices(self, interaction: discord.Interaction, request_reward_data: CommandData):
    try:
      request_reward_data.current_reward_choice = 'type'
      request_reward_data.selected_reward = {}
      choices = sorted(request_reward_data.current_level.get('reward_choices'), key=lambda x:x['grade'])
      request_reward_data.view = self.ButtonChoiceView(self, selectable_choices=choices, request_reward_data=request_reward_data)
      await self.interaction_handler.send_view(interaction=interaction, content="\n ### Choississez le type de reward ###", view=request_reward_data.view)
    except Exception as e:
      print(f'Erreur: {e}')

  async def initial_view_with_single_choice(self, interaction: discord.Interaction, request_reward_data: CommandData):
    request_reward_data.current_reward_choice = request_reward_data.current_level.get('reward_choices')[0].get('choices')[0].get('name').lower()
    choices = sorted(request_reward_data.current_level.get('reward_choices')[0].get('choices')[0].get('choices'), key=lambda x:x['grade'])
    initial_view_content = f'\n### Choix {request_reward_data.current_reward_choice} pour le type de reward {request_reward_data.selected_reward.get('type')} : ###'
    request_reward_data.view = self.ButtonChoiceView(self, selectable_choices=choices, request_reward_data=request_reward_data)
    await self.interaction_handler.send_view(interaction=interaction, content=initial_view_content, view=request_reward_data.view)

  async def build_initial_view(self, interaction: discord.Interaction, request_reward_data: CommandData):
    try:
      if len(request_reward_data.current_level.get('reward_choices')) > 1:
        await self.initial_view_with_multiple_choices(interaction=interaction, request_reward_data=request_reward_data)
        return
      request_reward_data.selected_reward = {'type' : request_reward_data.current_level.get('reward_choices')[0].get('name')}
      if 'choices' in request_reward_data.current_level.get('reward_choices')[0].keys():
        if len(request_reward_data.current_level.get('reward_choices')[0].get('choices')[0].get('choices')) > 1:
          await self.initial_view_with_single_choice(interaction=interaction, request_reward_data=request_reward_data)
          return
        else:
          request_reward_data.selected_reward['quality'] = request_reward_data.current_level.get('reward_choices')[0].get('choices')[0].get('choices')[0].get('name')
      await self.build_quantity_modal(interaction=interaction, request_reward_data=request_reward_data)
    except Exception as e:
      print(f'Erreur: {e}')
    
  async def build_quantity_modal(self, interaction: discord.Interaction, request_reward_data: CommandData):
    quantity_content = f'Choix de la quantité de {request_reward_data.selected_reward.get('type')}'
    request_reward_data.modal = self.InputModal(outer=self, title=quantity_content, request_reward_data=request_reward_data)
    await self.interaction_handler.send_modal(interaction=interaction, modal=request_reward_data.modal)

  async def build_validation_view(self, interaction:discord.Interaction, request_reward_data: CommandData):
    request_reward_data.view = self.ValidationView(outer=self, request_reward_data=request_reward_data)
    await self.interaction_handler.send_view(interaction=interaction, content=self.build_final_content(request_reward_data=request_reward_data), view=request_reward_data.view)

  def build_final_content(self, request_reward_data: CommandData):
    content = f'# {request_reward_data.current_level.get('name')} #\n'
    content += f'Vous êtes sur le point d\'ajouter {request_reward_data.times} fois '
    if 'quantity' in request_reward_data.selected_reward.keys():
      content += str(int_to_str(request_reward_data.selected_reward.get('quantity')))
      if 'quality' in request_reward_data.selected_reward.keys():
        content += f' {request_reward_data.selected_reward.get('quality')}'
      content += f' {request_reward_data.selected_reward.get('type')}'
    else:
      content += f'{request_reward_data.selected_reward.get('quality')} {request_reward_data.selected_reward.get('item')}'
    content += '. Voulez-vous valider ?'
    return content   
   
  async def setup(self, param_list=None):
    if param_list is None:
      self.levels = await self.bot.back_requests.call('getAllLevels', False)
    else:
      self.levels = param_list
    self.levelname_choices = CommandService.set_choices_by_rewards(self.levels)

async def setup(bot):
  await bot.add_cog(Reward(bot))