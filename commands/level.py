import typing
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, Select

from service.command import CommandService
from utils.sendMessage import SendMessage


class Level(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.level_command = next((c for c in bot.static_data.commands if c['name'] == 'level'), None)

    self.command_service = CommandService()
    CommandService.init_command(self.level_app_command, self.level_command)
    self.levelname_choices = None
    self.reward_types = None
    self.current_rewards = []
    self.global_selected_rewards = []
    self.current_reward_name = ''
    self.view = None
    

  class ChoiceView(discord.ui.View):
    def __init__(self, outer, button_data: 'Level.ButtonData'):
      print('Création de la vue')
      super().__init__(timeout=180)
      self.outer = outer
      self.button_data = button_data
      self.selectable_choices = button_data.selectable_choices
      
      for choice in self.selectable_choices:
        icon = choice.get('icon')
        label = choice.get('name')
        grade = choice.get('grade', 0)
        is_selected = choice.get('name') in self.selectable_choices
        self.add_item(self.outer.ChoiceButton(outer=self.outer, icon=icon, label=label, button_data=button_data, grade=grade, is_selected=is_selected))

      self.outer.current_rewards = []
      print(f'current rewards: {self.outer.current_rewards}')
      print('vue créée')
    
    def check_choice(self, list_to_check) -> bool:
      for to_check in list_to_check:
        if 'remaining_choices' in to_check.keys():
          remaining = to_check.get('remaining_choices')
          if (remaining == 1 and self.outer.current_reward_name != to_check.get('name')) or remaining > 1:
            print(f'encore des choix dans {to_check.get('name')}')
            return False
      return True
    
    def are_all_choices_done(self) -> bool:
      if not self.check_choice(self.outer.global_selected_rewards):
        return False
      if not self.check_choice(self.outer.current_rewards):
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
        self.add_item(self.outer.ValidateButton(outer=self.outer, button_data=self.button_data, label='submit'))
        print('bouton submit ajouté')
      if next_button:
        self.remove_item(next_button)
        print('bouton next supprimé')
    
    def add_next(self, submit_button, next_button):
      if not next_button:
        self.add_item(self.outer.ValidateButton(outer=self.outer, button_data=self.button_data, label='next'))
        print('bouton next ajouté')
      if submit_button:
        self.remove_item(submit_button)
        print('bouton submit supprimé')

    def remove_both_buttons(self, submit_button, next_button):
      if submit_button:
        self.remove_item(submit_button)
        print('bouton submit supprimé')
      elif next_button:
        self.remove_item(next_button)
        print('bouton next supprimé')  
      else:
        print('rien à supprimer')
  
    async def manage_validate_buttons(self, interaction):
      print('check des boutons de validation')
      submit_button = self.return_validate_buttons('submit')
      next_button = self.return_validate_buttons('next')

      if len(self.outer.current_rewards) > 0 :
        if self.are_all_choices_done():
          self.add_submit(submit_button, next_button)
        else:
          self.add_next(submit_button, next_button)
      else:
        self.remove_both_buttons(submit_button, next_button)

      await interaction.response.edit_message(view=self)

      
  class ChoiceButton(Button):
    def __init__(self, outer, icon: str, label: str, button_data:'Level.ButtonData', grade: int = None ,is_selected: bool = False):
      print(f'build choice button : {label}')
      style = discord.ButtonStyle.primary if is_selected else discord.ButtonStyle.secondary
      super().__init__(label=label, style=style, custom_id=label)
      
      self.outer = outer
      self.icon = icon
      self.grade = grade
      self.selectable_choices = button_data.selectable_choices
      self.button_data = button_data
      self.is_selected = is_selected
      self.label = label

    async def callback(self, interaction: discord.Interaction):
      self.is_selected = not self.is_selected
      self.style = discord.ButtonStyle.primary if self.is_selected else discord.ButtonStyle.secondary
      
      to_check = {'name': self.label, 'icon': self.icon, 'grade': self.grade}
      found_reward = next((r for r in self.selectable_choices if r.get('name') == self.label), None)
      if 'choices' in found_reward.keys():
        to_check['remaining_choices'] = len(found_reward.get('choices'))
      else:
        to_check['remaining_choices'] = 0
      print(f'check si la reward est dans les éléments sélectionnés : {to_check}')

      if self.is_selected:
        self.outer.current_rewards.append(to_check)
      else:
        self.outer.current_rewards.remove(to_check)

      await self.outer.ChoiceView.manage_validate_buttons(self.outer.view, interaction)

  class ValidateButton(Button):
    def __init__(self, outer, button_data:'Level.ButtonData', label):
      super().__init__(label=label, style=discord.ButtonStyle.success, custom_id=label)
      self.outer = outer
      self.selectable_choices = button_data.selectable_choices
      self.button_data = button_data
      self.label = label

    async def callback(self, interaction: discord.Interaction):
      if self.label == 'submit':
        await self.submit_new_level(interaction)
      else:
        await self.display_next_view(interaction)

    async def display_next_view(self, interaction):
      self.append_current_choices()
      next_view_choices = self.select_next_view()
      next_choices_content = f'\n### Choix des {next_view_choices.get('name')} pour le type de reward {self.outer.current_reward_name} : ###'
      
      self.outer.view = self.outer.ChoiceView(outer=self.outer, button_data=self.outer.ButtonData(selectable_choices=next_view_choices.get('choices')))
      await interaction.response.edit_message(content=next_choices_content, embed=None, view=self.outer.view)
    
    def append_main_view_choices(self):
      print('append check vue globale')
      for crw in self.outer.current_rewards:
        remaining = crw.get('remaining_choices')
        if remaining > 0:
          crw['choices'] = []
          if remaining > 1:
            gr = next((r for r in self.outer.reward_types if r.get('name') == crw.get('name')), None)
            if gr is not None:
              for cr in gr.get('choices'):
                crw['choices'].append({'name': cr.get('name'), 'grade': cr.get('grade'), 'choices': []})
        self.outer.global_selected_rewards.append(crw)

    def append_with_no_choices_left(self, item):
      del item['remaining_choices']
      for cr in self.outer.current_rewards:
        del cr['remaining_choices']
        item.get('choices').append(cr)
      return item
    
    def append_with_choices_left(self, item):
      print(f'remains : {item['remaining_choices']}')
      gr = next((r for r in self.outer.reward_types if r.get('name') == self.outer.current_reward_name), None)
      gr_choices = gr['choices']
      choices_iter = len(gr_choices) - item['remaining_choices']
      item['choices'][choices_iter] = {'name': gr_choices[choices_iter].get('name'), 'icon': gr_choices[choices_iter].get('icon'), 'grade': gr_choices[choices_iter].get('grade'), 'choices': []}
      for cr in self.outer.current_rewards:
        del cr['remaining_choices']
        item['choices'][choices_iter]['choices'].append(cr)
      item['remaining_choices'] -= 1
      if item['remaining_choices'] == 0:
        del item['remaining_choices']
    
    def append_child_view_choices(self):
      print(f'append check vue enfant : {self.outer.current_reward_name}')
      
      gsrw = next((r for r in self.outer.global_selected_rewards if r.get('name') == self.outer.current_reward_name), None)
      if gsrw.get('remaining_choices') == 1 and len(gsrw.get('choices')) == 0:
        gsrw = self.append_with_no_choices_left(gsrw)
      else:
        gsrw = self.append_with_choices_left(gsrw)

    def append_current_choices(self):
      if self.outer.current_reward_name == '':
        self.append_main_view_choices()
      else:
        self.append_child_view_choices()
      print(f'Choix sauvegardés : {self.outer.global_selected_rewards}')

    def select_next_view(self):
      for gsrw in [s for s in self.outer.global_selected_rewards if 'remaining_choices' in s.keys()]:
        if gsrw.get('remaining_choices') == 0:
          del gsrw['remaining_choices']
        else:
          next_view = next((s for s in self.outer.reward_types if s.get('name') == gsrw.get('name')), None)
          self.outer.current_reward_name = next_view.get('name')
          print(f'Nouvelle vue : {self.outer.current_reward_name}')
          return next_view.get('choices')[len(next_view.get('choices')) - gsrw.get('remaining_choices')]
        
    async def submit_new_level(self, interaction):
      self.append_current_choices()
      """#TODO : créer le level :)"""
      print(f'CHOIX TERMINES !\n{self.outer.global_selected_rewards}')
      response = {'title': '', 'description': f"# Le niveau level.get('name') a été ajouté#\nMerci d'avoir ajouté ce niveau ! :kissing_heart:", 'color': 'blue'}
      await self.outer.send_message.update_remove_view(interaction, response)
     

  class ButtonData:
    def __init__(self, selectable_choices):
      self.selectable_choices = selectable_choices

  """async def level_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await self.command_service.return_autocompletion(self.level_choices, current)

  @app_commands.autocomplete(name=level_autocomplete)"""
  @app_commands.command(name='level')
  async def level_app_command(self, interaction: discord.Interaction, name: str, standard_energy_cost: int, coop_energy_cost: int):
    self.logger.command_log('level', interaction)
    self.logger.log_only('debug', f"name : {name} | standard_energy_cost : {standard_energy_cost} | coop_energy_cost : {coop_energy_cost}")
    author = str(interaction.user)
    if "spirou" not in author and "prep" not in author:
      await self.send_message.error(interaction, "Cette commande n'est pas publique pour l'instant", "Veuillez contacter Prep ou Spirou pour ajouter votre niveau à la liste.")
      self.logger.log_only('debug', f"user {author} non autorisé")
      self.logger.ok_log('level')
      return

    await self.send_message.post(interaction)
    response = await self.get_level_response(interaction, name, standard_energy_cost, coop_energy_cost)
    #await self.bot.update_service.command_setup_updater(['level'], False)
    #await self.send_message.update(interaction, response)
    self.logger.ok_log('level')

  async def get_level_response(self, interaction, level_name, standard_energy_cost, coop_energy_cost):
    """if level_name in [c.name for c in self.choices]:
      self.logger.log_only('debug', f"level déjà existant")
      return {'title': '', 'description': f"# Le niveau {level_name} existe déjà #\nTout est prêt pour l'utilisation des commandes reward et reward-stat :wink:", 'color': 'blue'}"""

    await self.build_initial_view(interaction)
    
    #level = await self.create_level(level_name, standard_energy_cost, coop_energy_cost)
    return {'title': '', 'description': f"# Le niveau level.get('name') a été ajouté#\nMerci d'avoir ajouté ce niveau ! :kissing_heart:", 'color': 'blue'}
  
  async def build_initial_view(self, interaction):
    self.current_rewards = []
    self.global_selected_rewards = []
    self.current_reward_name = ''
    self.view = self.ChoiceView(self, button_data=self.ButtonData(selectable_choices=self.reward_types))
    await interaction.edit_original_response(content="\n ### Choississez le(s) type(s) de reward ###", embed=None, view=self.view)

  async def create_level(self, name, standard_energy_cost, coop_energy_cost):
    data = {
      "name": name,
      "standard_energy_cost": standard_energy_cost,
      "coop_energy_cost": coop_energy_cost
    }
    return await self.bot.back_requests.call('addLevel', False, [data])
      
  async def setup(self, param_list):
    #if param_list is None:
    #  choices = await self.bot.back_requests.call('getAllLevels', False)
    #else:
    #  choices = param_list
    self.reward_types = await self.bot.back_requests.call('getAllRewardTypes', False)
    #self.levelname_choices = CommandService.set_choices([{'name': c.get('name')} for c in choices]) 

async def setup(bot):
  await bot.add_cog(Level(bot))