import typing
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button
import emoji
import re

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
      super().__init__(timeout=180)
      self.outer = outer
      self.button_data = button_data
      self.selectable_choices = button_data.selectable_choices
      
      for choice in self.selectable_choices:
        icon = choice.get('icon') or ''
        label = choice.get('name')
        grade = choice.get('grade', 0)
        has_quantity = choice.get('has_quantity', None)
        is_selected = choice.get('name') in self.selectable_choices
        self.add_item(self.outer.ChoiceButton(outer=self.outer, icon=icon, label=label, button_data=button_data, grade=grade, has_quantity=has_quantity, is_selected=is_selected))

      self.outer.current_rewards = []
    
    def check_choice(self, list_to_check) -> bool:
      for to_check in list_to_check:
        if 'remaining_choices' in to_check.keys():
          remaining = to_check.get('remaining_choices')
          if (remaining == 1 and self.outer.current_reward_name != to_check.get('name')) or remaining > 1:
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
      if next_button:
        self.remove_item(next_button)
    
    def add_next(self, submit_button, next_button):
      if not next_button:
        self.add_item(self.outer.ValidateButton(outer=self.outer, button_data=self.button_data, label='next'))
      if submit_button:
        self.remove_item(submit_button)

    def remove_both_buttons(self, submit_button, next_button):
      if submit_button:
        self.remove_item(submit_button)
      elif next_button:
        self.remove_item(next_button)
  
    async def manage_validate_buttons(self, interaction):
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
    def __init__(self, outer, icon: str, label: str, button_data:'Level.ButtonData', grade: int = None, has_quantity: bool = None, is_selected: bool = False):
      style = discord.ButtonStyle.primary if is_selected else discord.ButtonStyle.secondary
      super().__init__(label=label, style=style, custom_id=label)

      if not outer.current_reward_name == '':
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
      
      to_check = {'name': self.label, 'icon': self.icon, 'grade': self.grade, 'has_quantity': self.has_quantity}
      found_reward = next((r for r in self.selectable_choices if r.get('name') == self.label), None)
      if 'choices' in found_reward.keys():
        to_check['remaining_choices'] = len(found_reward.get('choices'))
      else:
        to_check['remaining_choices'] = 0

      if self.is_selected:
        self.outer.current_rewards.append(to_check)
      else:
        self.outer.current_rewards.remove(to_check)

      await self.outer.ChoiceView.manage_validate_buttons(self.outer.view, interaction)

    def get_emoji_from_icon(self, icon):
      if 'customIcon' in icon or icon == '':
        return None
      unicode_match = re.match(r'\\U([0-9a-fA-F]{8})', icon)
      if unicode_match:
        return chr(int(unicode_match.group(1), 16))
      return emoji.emojize(icon)

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
      gr = next((r for r in self.outer.reward_types if r.get('name') == self.outer.current_reward_name), None)
      gr_choices = gr['choices']
      choices_iter = 0
      item['choices'].append({'name': gr_choices[choices_iter].get('name'), 'icon': gr_choices[choices_iter].get('icon'), 'grade': gr_choices[choices_iter].get('grade'), 'choices': []})
      del item['remaining_choices']
      for cr in self.outer.current_rewards:
        del cr['remaining_choices']
        item.get('choices')[0].get('choices').append(cr)
      return item
    
    def append_with_choices_left(self, item):
      gr = next((r for r in self.outer.reward_types if r.get('name') == self.outer.current_reward_name), None)
      gr_choices = gr['choices']
      choices_iter = len(gr_choices) - item['remaining_choices']
      item['choices'][choices_iter] = {'name': gr_choices[choices_iter].get('name'), 'icon': gr_choices[choices_iter].get('icon'), 'grade': gr_choices[choices_iter].get('grade'), 'choices': []}
      if len(gr_choices) == 1 and item.get('remaining_choices') == 1:
        return
      
      for cr in self.outer.current_rewards:
        del cr['remaining_choices']
        item['choices'][choices_iter]['choices'].append(cr)
      item['remaining_choices'] -= 1
      if item['remaining_choices'] == 0:
        del item['remaining_choices']
    
    def append_child_view_choices(self):     
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

    def select_next_view(self):
      for gsrw in [s for s in self.outer.global_selected_rewards if 'remaining_choices' in s.keys()]:
        if gsrw.get('remaining_choices') == 0:
          del gsrw['remaining_choices']
        else:
          next_view = next((s for s in self.outer.reward_types if s.get('name') == gsrw.get('name')), None)
          self.outer.current_reward_name = next_view.get('name')
          return next_view.get('choices')[len(next_view.get('choices')) - gsrw.get('remaining_choices')]
        
    async def submit_new_level(self, interaction):
      self.append_current_choices()
      await self.outer.create_level()
      response = {'title': '', 'description': f"# Le niveau {self.outer.name} a été ajouté#\nMerci d'avoir ajouté ce niveau ! :kissing_heart:", 'color': 'blue'}
      await self.outer.send_message.update_remove_view(interaction, response)
      self.logger.ok_log('level')
     

  class ButtonData:
    def __init__(self, selectable_choices):
      self.selectable_choices = selectable_choices

  async def level_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    return await self.command_service.return_autocompletion(self.levelname_choices, current)

  @app_commands.autocomplete(name=level_autocomplete)
  @app_commands.command(name='level')
  async def level_app_command(self, interaction: discord.Interaction, name: str, standard_energy_cost: int = None, coop_energy_cost: int = None):
    self.logger.command_log('level', interaction)
    self.logger.log_only('debug', f"name : {name} | standard_energy_cost : {standard_energy_cost} | coop_energy_cost : {coop_energy_cost}")
    author = str(interaction.user)
    if "spirou" not in author and "prep" not in author:
      await self.send_message.error(interaction, "Cette commande n'est pas publique pour l'instant", "Veuillez contacter Prep ou Spirou pour ajouter votre niveau à la liste.")
      self.logger.log_only('debug', f"user {author} non autorisé")
      self.logger.ok_log('level')
      return
    
    await self.send_message.post(interaction)
    
    self.name = name
    self.standard_energy_cost = standard_energy_cost
    self.coop_energy_cost = coop_energy_cost
    self.interaction = interaction

    await self.get_level_response(interaction)

  async def get_level_response(self, interaction):
    if self.name in [c.name for c in self.levelname_choices]:
      self.logger.log_only('debug', f"level déjà existant")
      response = {'title': '', 'description': f"# Le niveau {self.name} existe déjà #\nTout est prêt pour l'utilisation des commandes reward et rewardstat :wink:", 'color': 'blue'}
      await self.send_message.update(interaction, response)
      self.logger.ok_log('level')
      return
    
    if self.standard_energy_cost is None and self.coop_energy_cost is None:
      self.logger.log_only('debug', f"paramètres manquants")
      response = {'title': '', 'description': f"# Erreur #\nUn level doit avoir au moins un coût en énergie (standard ou coop)", 'color': 'red'}
      await self.send_message.update(interaction, response)
      self.logger.ok_log('level')
      return

    await self.build_initial_view(interaction)
  
  async def build_initial_view(self, interaction):
    self.current_rewards = []
    self.global_selected_rewards = []
    self.current_reward_name = ''
    self.view = self.ChoiceView(self, button_data=self.ButtonData(selectable_choices=self.reward_types))
    await interaction.edit_original_response(content="\n ### Choississez le(s) type(s) de reward ###", embed=None, view=self.view)

  async def create_level(self):
    gear = next((g for g in self.global_selected_rewards if g.get('name') == 'gear'), None)
    if gear is not None:
      types = ','.join([hero_type.get('name') for hero_type in gear.get('choices')[0].get('choices')])
      positions = ','.join([gear_position.get('name') for gear_position in gear.get('choices')[2].get('choices')])
      items = await self.bot.back_requests.call('getUniqueGearByTypeAndPosition', False, [types, positions])
      items = sorted(items, key=lambda i: i.get('name'))

      item_choices = []
      for i in range(len(items)):
        item_choices.append({'name': items[i].get('name'), 'icon': '', 'grade': i})
      gear['choices'] = [gear.get('choices')[1], {'name': 'Item', 'icon': '', 'grade': 3, 'choices': item_choices}]
      
    data = {
      "name": self.name,
      "standard_energy_cost": self.standard_energy_cost,
      "coop_energy_cost": self.coop_energy_cost,
      "reward_choices": self.global_selected_rewards
    }
    await self.bot.back_requests.call('addLevel', False, [data])
    await self.bot.update_service.command_setup_updater(['level'], False)
      
      
  async def setup(self, param_list):
    if param_list is None:
      choices = await self.bot.back_requests.call('getAllLevels', False)
    else:
      choices = param_list
    self.reward_types = await self.bot.back_requests.call('getAllRewardTypes', False)
    self.levelname_choices = CommandService.set_choices_by_rewards(choices) 

async def setup(bot):
  await bot.add_cog(Level(bot))