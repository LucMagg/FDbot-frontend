from typing import Optional, List
from discord import app_commands
from collections import defaultdict

from utils.str_utils import str_to_slug

class CommandService:
  def __init__(self, bot):
    self.bot = bot

  # Build command payload parts
  def build_command_payload(self, command, command_data: Optional[dict] = None, is_root: bool = True) -> dict:
    command_data = command_data or {}
    payload = {
      'name': command.name,
      'description': command_data.get('description', command.description),
      'type': command_data.get('type', 1),
    }
    if is_root:
      payload['nsfw'] = False
      payload['dm_permission'] = True
    for key in ('name_localizations', 'description_localizations'):
      val = command_data.get(key)
      if val:
        payload[key] = val
    options_data = {self._normalize(opt.get('name')): opt for opt in command_data.get('options', []) if opt.get('name')}
    options = []
    if isinstance(command, app_commands.Group):
      for subcmd in command.commands:
        sub_data = options_data.get(self._normalize(subcmd.name), {})
        options.append(self.build_command_payload(subcmd, sub_data, False))
    elif isinstance(command, app_commands.Command):
      for param in command.parameters:
        param_data = options_data.get(self._normalize(param.name))
        options.append(self._build_param_payload(param, param_data))
    if options:
      payload['options'] = options
    return payload

  def _build_param_payload(self, param, param_data: Optional[dict] = None) -> dict:
    param_data = param_data or {}
    opt = {
      'type': param_data.get('type', param.type.value),
      'name': param_data.get('name', param.name),
      'description': param_data.get('description', param.description),
      'required': param_data.get('required', getattr(param, 'required', False))
    }
    if getattr(param, 'autocomplete', False):
      opt['autocomplete'] = True
    for key in ('name_localizations', 'description_localizations'):
      val = param_data.get(key)
      if val:
        opt[key] = val
    if param_data.get('choices'):
      opt['choices'] = []
      for choice in param_data['choices']:
        choice_dict = {'name': choice['name'], 'value': choice['value']}
        if choice.get('name_localizations'):
          choice_dict['name_localizations'] = choice['name_localizations']
        opt['choices'].append(choice_dict)
    return opt
  
  def _normalize(self, name: str) -> str:
    return name.lower() if name else name
    
  
  # Set command choices parts
  async def set_choices(self, whichone: list[str]):
    collection_by_langcode = {}
    for w in whichone:
      match w:
        case 'heroes':
          collection_by_langcode = await self._get_list_choices(request='getAllHeroes', choices=collection_by_langcode)
        case 'pets':
          collection_by_langcode = await self._get_list_choices(request='getAllPets', choices=collection_by_langcode)
        case 'classes':
          collection_by_langcode = await self._get_list_choices(request='getAllClasses', choices=collection_by_langcode)
        case 'exclusives':
          collection_by_langcode = await self._get_list_choices(request='getExclusiveTypes', choices=collection_by_langcode)
        case 'items':
          collection_by_langcode = await self._get_list_choices(request='getAllExistingGear', choices=collection_by_langcode)
        case 'levels':
          collection_by_langcode = await self._get_list_choices(request='getAllLevels', choices=collection_by_langcode)
        case 'sorted levels':
          return await self._set_levels_sorted_by_rewards()
        case 'merc users':
          return await self._set_merc_user_choices()
        case 'merc heroes':
          return await self._set_merc_hero_choices()
        case 'talents':
          collection_by_langcode = await self._get_list_choices(request='getHeroesAndPetsTalents', choices=collection_by_langcode)
        case 'languages':
          collection_by_langcode = await self._get_list_choices(request='getAllLanguages', choices=collection_by_langcode)
        case 'dc levels':
          return await self._set_dc_levels()
        case _:
          return
    if 'sorted levels' in whichone:
      return {lang: self.set_choices_by_rewards(lang, collection) for lang, collection in collection_by_langcode.items()}
    return {lang: sorted((app_commands.Choice(name=c['name'], value=c['name_slug']) for c in collection), key=lambda c: c.name) for lang, collection in collection_by_langcode.items()}
  
  async def _get_list_choices(self, request: str, choices: dict | None = None) -> dict:
    if choices is None:
      choices = {}
    collection = await self.bot.back_requests.call(request)
    for language in self.bot.static_data.languages:
      code = language.get('code')
      if code not in choices:
        choices[code] = []
      if not collection:
        error = self.bot.language.translate_from_key(text_to_translate=f'Loading {request.lower()[6:]} failure', lang=code)
        choices[code].append({'name': error, 'name_slug': error})

      match request:
        case 'getAllClasses':
          items = [{'name': self.bot.language.translate_from_key(text_to_translate=f"{c['heroclass']} S", lang=code), 'name_slug': c['heroclass']} for c in collection]
        case 'getExclusiveTypes':
          items = [{'name': self.bot.language.translate_from_key(text_to_translate=c, lang=code), 'name_slug': c} for c in collection]
          all_value = self.bot.language.translate_from_key(text_to_translate='all', lang=code).capitalize()
          items.append({'name': all_value, 'name_slug': all_value})
        case 'getAllExistingGear':
          items = [{'name': self.bot.language.translate_from_key(text_to_translate=c, lang=code), 'name_slug': c} for c in collection]
        case 'getAllLevels':
          items = [{'name': c.get('name').get(code, 'en'), 'name_slug': c.get('name_slug')} for c in collection]
        case 'getHeroesAndPetsTalents':
          items = [{'name': self.bot.language.translate_from_key(text_to_translate=c.get('name'), lang=code), 'name_slug': c.get('name')} for c in collection]
        case 'getAllLanguages':
          items = [{'name': self.bot.language.translate_from_key(text_to_translate=c.get('name'), lang=code), 'name_slug': c.get('code')} for c in collection]
        case _:
          items = [{'name': self.bot.language.translate_from_key(text_to_translate=c['name'], lang=code), 'name_slug': c['name_slug']} for c in collection]
      choices[code].extend(items)

      help_value = self.bot.language.translate_from_key(text_to_translate='help', lang=code).capitalize()
      choices[code].append({'name': help_value, 'name_slug': help_value})

      if {'name': '', 'name_slug': ''} in choices[code]:
        choices[code].remove({'name': '', 'name_slug': ''})
    return choices
  
  async def _set_merc_user_choices(self):
    collection_by_langcode = {}
    raw_users = await self.bot.back_requests.call('getAllMercUsers')
    if 'error' in raw_users:
      for language in self.bot.static_data.languages:
        collection_by_langcode[language.get('code')] = []
      return collection_by_langcode
    for language in self.bot.static_data.languages:
      lang = language.get('code')
      collection = defaultdict(list)
      for user in raw_users:
        collection[user.get('guild_id')].append(app_commands.Choice(name=user.get('user'), value=str(user.get('user_id'))))
      help_value = self.bot.language.translate_from_key(text_to_translate='help', lang=lang).capitalize()
      for guild_id, choices in collection.items():
        choices.append(app_commands.Choice(name=help_value, value=help_value))
        collection[guild_id] = sorted(choices, key=lambda c: c.name.lower())
      collection_by_langcode[lang] = dict(collection)
    return collection_by_langcode
  
  async def _set_merc_hero_choices(self):
    collection_by_langcode = {}
    mercs_by_guild = await self.bot.back_requests.call('getAllUniqueMercs')
    if 'error' in mercs_by_guild:
      for language in self.bot.static_data.languages:
        collection_by_langcode[language.get('code')] = []
      return collection_by_langcode
    for language in self.bot.static_data.languages:
      lang = language.get('code')
      collection = defaultdict(list)
      for guild in mercs_by_guild:
        collection[guild.get('guild_id')] = [app_commands.Choice(name=m, value=str_to_slug(m)) for m in guild.get('mercs')]
      help_value = self.bot.language.translate_from_key(text_to_translate='help', lang=lang).capitalize()
      for guild_id, choices in collection.items():
        choices.append(app_commands.Choice(name=help_value, value=help_value))
        collection[guild_id] = sorted(choices, key=lambda c: c.name.lower())
      collection_by_langcode[lang] = dict(collection)
    return collection_by_langcode
  
  async def _set_levels_sorted_by_rewards(self):
    levels = await self.bot.back_requests.call('getAllLevels')
    collection_by_langcode = {}
    for language in self.bot.static_data.languages:
      lang = language.get('code')
      def sort_function(level):
        return sum(r.get('total_appearances', 0) for r in level.get('rewards', []))
      sorted_levels = sorted(levels, key=lambda l: sort_function(l), reverse=True)
      choices = [app_commands.Choice(name=l.get('name').get(lang, l.get('name').get('en', 'No name')), value=l.get('name_slug')) for l in sorted_levels]
      help_value = self.bot.language.translate_from_key(text_to_translate='help', lang=lang).capitalize()
      choices.append(app_commands.Choice(name=help_value, value=help_value))
      collection_by_langcode[lang] = choices
    return collection_by_langcode
  
  async def _set_dc_levels(self):
    levels = await self.bot.back_requests.call('getAllDC')
    if not 'error' in levels:
      existing_numbers = {int(l.get('name')) for l in levels if l.get('name', '').isdigit()}
    else:
      existing_numbers = {}
    all_levels_collection_by_langcode = {}
    existing_levels_collection_by_langcode = {}
    for language in self.bot.static_data.languages:
      lang = language.get('code')
      help_value = self.bot.language.translate_from_key(text_to_translate='help', lang=lang).capitalize()
      existing_choices = [app_commands.Choice(name=str(n), value=str(n)) for n in range(1, 301) if n in existing_numbers]
      existing_choices.append(app_commands.Choice(name=help_value, value=help_value))
      existing_levels_collection_by_langcode[lang] = existing_choices
      all_choices = [app_commands.Choice(name=str(n), value=str(n)) for n in range(1, 301)]
      all_choices.append(app_commands.Choice(name=help_value, value=help_value))
      all_levels_collection_by_langcode[lang] = all_choices
    return all_levels_collection_by_langcode, existing_levels_collection_by_langcode

  async def return_autocompletion(self, choices: list, current: str) -> List[app_commands.Choice[str]]:
    first_25_choices = [c for c in choices if current.lower() in c.name.lower()][:25]
    return first_25_choices