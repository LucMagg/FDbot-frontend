import typing
import discord
from discord.utils import MISSING
import emoji
import re

from typing import Optional
from discord.app_commands import Choice

from discord.ext import commands
from discord import app_commands
from discord.ui import Button, TextInput

from service.command import CommandService
from utils.message import Message
from utils.str_utils import str_to_slug, str_to_int, int_to_str
from utils.misc_utils import get_discord_color

class Reward(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.message = Message(bot)
    self.reward_command = next((c for c in bot.static_data.commands if c['name'] == 'reward'), None)

    self.command_service = CommandService()
    CommandService.init_command(self.reward_app_command, self.reward_command)
    self.levels = None
    self.levelname_choices = None
    
    self.current_level = None
    self.current_reward_choice = None
    self.selected_reward = None
    self.view = None
    self.modal = None
    self.times = None


  class ChoiceView(discord.ui.View):
###### VUES DES CHOIX
    def __init__(self, outer, button_data: 'Reward.ButtonData'):
      super().__init__(timeout=180)
      self.outer = outer
      self.button_data = button_data
      self.selectable_choices = button_data.selectable_choices
      
      for choice in self.selectable_choices:
        icon = choice.get('icon') if self.outer.current_reward_choice != 'type' else ''
        label = choice.get('name')
        grade = choice.get('grade', 0)
        has_quantity = choice.get('has_quantity', None)
        is_selected = choice.get('name') in self.selectable_choices
        self.add_item(self.outer.ChoiceButton(outer=self.outer, icon=icon, label=label, button_data=button_data, grade=grade, has_quantity=has_quantity, is_selected=is_selected))     

    def has_one_selected(self) -> bool:
      for button in self.children:
        if isinstance(button, discord.ui.Button):
          if button.custom_id not in ['submit', 'next'] and button.is_selected:
            return True
      return False
    
    def are_all_choices_done(self) -> bool:
      # rien n'est encore saisi -> False
      if not 'type' in self.outer.selected_reward.keys():
        return False
      # il y a encore des quantités à saisir -> False
      selected_choice = next((c for c in self.outer.current_level.get('reward_choices') if c.get('name') == self.outer.selected_reward.get('type')), None)
      if selected_choice.get('has_quantity'):
        return False      
      # il y a encore des choix à faire -> False
      last_choice = selected_choice.get('choices')[len(selected_choice.get('choices')) - 1]
      if self.outer.current_reward_choice != last_choice.get('name').lower():
        return False
      return True

    def return_validate_buttons(self, id):
      for button in self.children:
        if isinstance(button, discord.ui.Button):
          if button.custom_id == id:
            return button
      return False
    
    def add_submit(self, submit_button, next_button):
      if not submit_button:
        self.add_item(self.outer.ValidateButton(outer=self.outer, button_data=self.button_data, label='Valider'))
      if next_button:
        self.remove_item(next_button)
    
    def add_next(self, submit_button, next_button):
      if not next_button:
        self.add_item(self.outer.ValidateButton(outer=self.outer, button_data=self.button_data, label='Suivant'))
      if submit_button:
        self.remove_item(submit_button)

    def remove_both_buttons(self, submit_button, next_button):
      if submit_button:
        self.remove_item(submit_button)
      if next_button:
        self.remove_item(next_button)
  
    async def manage_validate_buttons(self, interaction):
      submit_button = self.return_validate_buttons('Valider')
      next_button = self.return_validate_buttons('Suivant')

      if self.has_one_selected():
        if self.are_all_choices_done():
          self.add_submit(submit_button, next_button)
        else:
          self.add_next(submit_button, next_button)
      else:
        self.remove_both_buttons(submit_button, next_button)
        
      await self.outer.response_manager.handle_response(interaction=interaction, view=self)

  class ChoiceButton(Button):
    def __init__(self, outer, icon: str, label: str, button_data:'Reward.ButtonData', grade: int = None, has_quantity: bool = None, is_selected: bool = False):
      style = discord.ButtonStyle.primary if is_selected else discord.ButtonStyle.secondary
      super().__init__(label=label, style=style, custom_id=str_to_slug(label))
      emoji = self.get_emoji_from_icon(icon)
      if emoji is not None:
        super().__init__(emoji=emoji)
      
      self.outer = outer
      self.has_quantity = has_quantity
      self.icon = icon
      self.grade = grade
      self.selectable_choices = button_data.selectable_choices
      self.button_data = button_data
      self.is_selected = is_selected
      self.label = label

    async def callback(self, interaction: discord.Interaction):
      self.is_selected = not self.is_selected
      self.style = discord.ButtonStyle.primary if self.is_selected else discord.ButtonStyle.secondary
      
      if self.is_selected:
        self.outer.selected_reward[self.outer.current_reward_choice] = self.label
        self.unselect_all_others(self.custom_id)
      else:
        if self.outer.current_reward_choice in self.outer.selected_reward.keys():
          del self.outer.selected_reward[self.outer.current_reward_choice]

      await self.outer.ChoiceView.manage_validate_buttons(self.outer.view, interaction)

    def unselect_all_others(self, selected_id):
      for button in self.outer.view.children:
        if isinstance(button, discord.ui.Button):
          if button.custom_id not in [selected_id, 'Valider', 'Suivant', str_to_slug('Ajouter une autre récompense')]:
            button.is_selected = False
            button.style = discord.ButtonStyle.secondary

    def get_emoji_from_icon(self, icon):
      if 'customIcon' in icon or icon == '':
        return None
      unicode_match = re.match(r'\\U([0-9a-fA-F]{8})', icon)
      if unicode_match:
        return chr(int(unicode_match.group(1), 16))
      return emoji.emojize(icon)

  class ValidateButton(Button):
    def __init__(self, outer, button_data:'Reward.ButtonData', label):
      super().__init__(label=label, style=discord.ButtonStyle.success, custom_id=label)
      self.outer = outer
      self.selectable_choices = button_data.selectable_choices
      self.button_data = button_data
      self.label = label

    async def callback(self, interaction: discord.Interaction):
      if self.label == 'Valider':
        await self.outer.build_validation_view(interaction)
      elif self.label == 'Suivant':
        await self.display_next_view(interaction)

    async def display_next_view(self, interaction):
      next_view_choices = self.select_next_view()
      
      if next_view_choices:
        next_choices_content = f'\n### Choix {self.outer.current_reward_choice} pour le type de reward {self.outer.selected_reward.get('type')} : ###'
        self.outer.view = self.outer.ChoiceView(outer=self.outer, button_data=self.outer.ButtonData(selectable_choices=next_view_choices, initial_interaction=interaction))
        await self.outer.response_manager.handle_response(interaction=interaction, content=next_choices_content, view=self.outer.view)
        return

      await self.outer.build_quantity_modal(interaction)

    def select_next_view(self):
      current_reward = next((c for c in self.outer.current_level.get('reward_choices') if c.get('name') == self.outer.selected_reward.get('type')), None)

      if self.outer.current_reward_choice == 'type':
        self.outer.current_reward_choice = current_reward.get('choices')[0].get('name').lower()
        return sorted(current_reward.get('choices')[0].get('choices'), key=lambda x:x['grade'])
      
      else:
        current_choices = current_reward.get('choices')
        next_choices = []
        try:
          for i, choice in enumerate(current_choices):
            if choice.get('name').lower() == self.outer.current_reward_choice:
              next_choices = current_choices[i + 1]
              break
        except:
          if len(next_choices) == 0:
            return False
        
        self.outer.current_reward_choice = next_choices.get('name').lower()
        return sorted(next_choices.get('choices'), key=lambda x: x['grade'])     
    
  class ButtonData:
    def __init__(self, selectable_choices, initial_interaction):
      self.selectable_choices = selectable_choices
      self.initial_interaction = initial_interaction
  


  class InputModal(discord.ui.Modal):
##### MODALE DE QUANTITÉ
    def __init__(self, outer, title:str):
      super().__init__(title=title)
      self.outer = outer
      
      self.input_quantity = self.outer.InputField(outer=self.outer, custom_id='input')
      self.add_item(self.input_quantity)

    async def on_submit(self, interaction: discord.Interaction):
      quantity = str_to_int(self.input_quantity.value)
      
      failed_because_of_bahabulle = False
      if quantity is None:
        failed_because_of_bahabulle = True
      if isinstance(quantity, int):
        if quantity <= 0:
          failed_because_of_bahabulle = True
      
      if failed_because_of_bahabulle:
        response = {'title': 'Erreur', 'description': f"{self.input_quantity.value} n'est pas une quantité valide, merci de recommencer :rolling_eyes:", 'color': 'red'}
        await self.outer.response_manager.handle_response(interaction=interaction, response=response)
        self.logger.ok_log('reward')
        return

      self.outer.selected_reward['quantity'] = quantity
      await self.outer.build_validation_view(interaction)
                            
  class InputField(TextInput):
    def __init__(self, outer, custom_id: str):
      super().__init__(label='Entrez une quantité', custom_id=custom_id, required=True)
      self.outer = outer

  class ValidationView(discord.ui.View):
##### VUE FINALE DE VALIDATION DE LA REWARD
    def __init__(self, outer):
      super().__init__(timeout=180)
      self.outer = outer
      self.add_item(self.outer.ManyTimesSelector(outer=self.outer))
      self.add_item(self.outer.CancelButton(outer=self.outer))
      self.add_item(self.outer.SubmitRewardButton(outer=self.outer))
  
  class ManyTimesSelector(discord.ui.Select):
    def __init__(self, outer):
      self.outer = outer
      super().__init__(custom_id='selector', placeholder=self.outer.times)

      for i in range(1,6):
        self.add_option(label=i, value=i)

    async def callback(self, interaction: discord.Interaction):
      self.outer.times = self.values[0]
      await self.outer.build_validation_view(interaction)
  
  class CancelButton(Button):
    def __init__(self, outer):
      super().__init__(style=discord.ButtonStyle.red, label='Annuler', custom_id='annuler')
      self.outer = outer

    async def callback(self, interaction: discord.Interaction):
      description = f'# {self.outer.current_level.get('name')} # \nRécompense annulée :)'
      response = {'title': '', 'description': description, 'color': 'red'}
      await self.outer.response_manager.handle_response(interaction=interaction, response=response)
      self.outer.logger.ok_log('reward')

  class SubmitRewardButton(Button):
    def __init__(self, outer):
      self.outer = outer
      super().__init__(style=discord.ButtonStyle.success, label=f'Ajouter {self.outer.times} fois', custom_id='submit')
      
    async def callback(self, interaction: discord.Interaction):
      self.outer.selected_reward['times'] = int(self.outer.times)
      response = await self.outer.bot.level_service.add_reward(emojis=interaction.guild.emojis, level_name=self.outer.current_level.get('name'), reward_data=self.outer.selected_reward)
      await self.outer.response_manager.handle_response(interaction=interaction, response=response)
      self.logger.ok_log('reward')

  class ResponseManager:
##### GESTION DES INTERACTIONS
    def __init__(self):
      self.initial_interaction = None
      self.last_content = None

    async def handle_response(self, interaction: discord.Interaction, response=None, content='', view=None, modal=None):
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


##### COMMANDE
  async def level_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await self.command_service.return_autocompletion(self.levelname_choices, current)

  @app_commands.autocomplete(level=level_autocomplete)
  @app_commands.command(name='reward')
  async def reward_app_command(self, interaction: discord.Interaction, level: str):
    self.logger.command_log('reward', interaction)
    self.logger.log_only('debug', f"level : {level}")

    await self.get_response(interaction, level)

  async def get_response(self, interaction, level_name):
    self.response_manager = self.ResponseManager()
    self.times = 1

    if level_name not in [cl.name for cl in self.levelname_choices]:
      self.logger.log_only('debug', 'level inexistant')
      response = {'title': 'Erreur', 'description': f'Le level {level_name} n\'existe pas.\nMerci de vérifier et/ou de contacter Spirou ou Prep pour la création du level si besoin :wink:', 'color': 'red'}
      await self.response_manager.handle_response(interaction=interaction, response=response)
      self.logger.ok_log('reward')
      return

    self.current_level = next((l for l in self.levels if str_to_slug(level_name) == l.get('name_slug')), None)
    await self.build_initial_view(interaction)

  async def initial_view_with_multiple_choices(self, interaction: discord.Interaction):
    self.current_reward_choice = 'type'
    self.selected_reward = {}
    choices = sorted(self.current_level.get('reward_choices'), key=lambda x:x['grade'])
    self.view = self.ChoiceView(self, button_data=self.ButtonData(selectable_choices=choices, initial_interaction=interaction))
    await self.response_manager.handle_response(interaction=interaction, content="\n ### Choississez le type de reward ###", view=self.view)

  async def initial_view_with_single_choice(self, interaction: discord.Interaction):
    self.current_reward_choice = self.current_level.get('reward_choices')[0].get('choices')[0].get('name').lower()
    choices = sorted(self.current_level.get('reward_choices')[0].get('choices')[0].get('choices'), key=lambda x:x['grade'])
    initial_view_content = f'\n### Choix {self.current_reward_choice} pour le type de reward {self.selected_reward.get('type')} : ###'
    self.view = self.ChoiceView(self, button_data=self.ButtonData(selectable_choices=choices, initial_interaction=interaction))
    await self.response_manager.handle_response(interaction=interaction, content=initial_view_content, view=self.view)

  async def build_initial_view(self, interaction: discord.Interaction):
    if len(self.current_level.get('reward_choices')) > 1:
      await self.initial_view_with_multiple_choices(interaction)
      return
    
    self.selected_reward = {'type' : self.current_level.get('reward_choices')[0].get('name')}

    if 'choices' in self.current_level.get('reward_choices')[0].keys():
      await self.initial_view_with_single_choice(interaction)
      return
    
    await self.build_quantity_modal(interaction)
    
  async def build_quantity_modal(self, interaction: discord.Interaction):
    quantity_content = f'Choix de la quantité de {self.selected_reward.get('type')}'
    self.modal = self.InputModal(outer=self, title=quantity_content)
    try:
      await self.response_manager.handle_response(interaction=interaction, modal=self.modal)
    except Exception as e:
      print(f'erreur : {e}')

  async def build_validation_view(self, interaction:discord.Interaction):
    try:
      self.view = self.ValidationView(outer=self)
      await self.response_manager.handle_response(interaction=interaction, content=self.build_final_content(), view=self.view)
    except Exception as e:
      print(f'erreur : {e}')

  def build_final_content(self):
    content = f'# {self.current_level.get('name')} #\n'
    content += f'Vous êtes sur le point d\'ajouter {self.times} fois '
    if 'quantity' in self.selected_reward.keys():
      content += str(int_to_str(self.selected_reward.get('quantity')))
      if 'quality' in self.selected_reward.keys():
        content += f' {self.selected_reward.get('quality')}'
      content += f' {self.selected_reward.get('type')}'
    else:
      content += f'{self.selected_reward.get('quality')} {self.selected_reward.get('item')}'
    content += '. Voulez-vous valider ?'
    return content
   
    
  async def setup(self, param_list):
    if param_list is None:
      self.levels = await self.bot.back_requests.call('getAllLevels', False)
    else:
      self.levels = param_list
    self.levelname_choices = CommandService.set_choices_by_rewards(self.levels)


async def setup(bot):
  await bot.add_cog(Reward(bot))