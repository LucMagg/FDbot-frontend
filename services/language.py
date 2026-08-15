import discord
from discord import app_commands, Locale
from discord.app_commands import TranslationContext, TranslationContextLocation

class LangService(app_commands.Translator):
  def __init__(self, bot):
    super().__init__()
    self.bot = bot
    self.languages = self._load_languages(bot.static_data.languages)
    self.langchannels = self._load_langchannels(bot.static_data.langchannels)
    self.key_dicts = {}
    self.value_dicts = {}
    self._build_all_translation_dicts()
    self.locale_mapping = {'fr': 'fr', 'en-US': 'en', 'en-GB': 'en'}

  def _load_languages(self, trad_db):
    languages = {}
    for doc in trad_db:
      code = doc.get('code')
      if not code:
        continue
      languages[code] = {}
      translations = doc.get('translations', {})      
      for section_name, section_data in translations.items():
        if isinstance(section_data, dict):
          for key, value in section_data.items():
            languages[code][key] = value    
    return languages

  def _load_langchannels(self, raw_langchannels):
    if not isinstance(raw_langchannels, list):
      self.bot.logger.log_only('warning', f'[LANG] Langchannels invalid or missing')
      return []
    return raw_langchannels
  
  def _build_all_translation_dicts(self):
    for lang in self.languages:
      self.key_dicts[lang] = {key.lower(): key for key in self.languages[lang]}
      self.value_dicts[lang] = {value.lower(): key for key, value in self.languages[lang].items()}
  
  def _apply_case(self, original: str, translation: str):
    if not original:
      return translation
    if original.isupper():
      return translation.upper()
    elif original.islower():
      return translation.lower()
    else:
      return translation

  def _translate_text(self, text_to_translate: str, translation_dict: dict, target_dict: dict):
    words = text_to_translate.split()
    result = []
    i = 0
    while i < len(words):
      max_length = len(words) - i
      found = False
      for length in range(max_length, 0, -1):
        word = ' '.join(words[i:i + length])
        if word.lower() in translation_dict:
          found_key = translation_dict[word.lower()]
          translated = self._apply_case(word, target_dict[found_key])
          result.append(translated)
          i += length
          found = True
          break
      if not found:
        result.append(words[i])
        i += 1
    return ' '.join(result)
    

  def translate_with_text(whichone: str, lang: str, trad_json):
    return trad_json[whichone][lang]  

  
  def translate_from_key(self, text_to_translate: str, lang: str):
    if lang not in self.languages:
      return text_to_translate
    return self._translate_text(text_to_translate, self.key_dicts[lang], self.languages[lang])
  

  def translate_from_value(self, text_to_translate: str, lang: str):
    if lang not in self.languages:
      return text_to_translate
    target_dict = {key: key for key in self.languages[lang]}
    return self._translate_text(text_to_translate, self.value_dicts[lang], target_dict)
  
  def set_language(self, interaction: discord.Interaction = None, channel_id: int = None):
    if interaction:
      code = next((l.get('code') for l in self.langchannels if l.get('channel_id') == interaction.channel_id), None)
      if code:
        return code
      return self.locale_mapping.get(str(interaction.locale), 'en')
    elif channel_id:
      code = next((l.get('code') for l in self.langchannels if l.get('channel_id') == channel_id), None)
      if code:
        return code
    return 'en'
    
  async def translate(self, string: app_commands.locale_str, locale: Locale, context: TranslationContext):
    lang_code = str(locale)
    if '_' in lang_code:
      lang_code = lang_code.split('_')[0]
    if '.' in lang_code:
      lang_code = lang_code.split('.')[1]
    lang_code = self.locale_mapping.get(lang_code, lang_code)
    
    if lang_code == 'en':
      return None
    if not context.data:
      return None
    
    if context.location in [TranslationContextLocation.command_name, TranslationContextLocation.command_description]:
      if not hasattr(context.data, 'name'):
        return None
      command_name = context.data.name
    else:
      if hasattr(context.data, 'command') and context.data.command:
        command_name = context.data.command.name
      else:
        return None
    
    command_data = next((c for c in self.bot.static_data.commands if c['name'] == command_name), None)
    if not command_data:
      return None

    if context.location == TranslationContextLocation.command_name:
      return command_data.get('name_localizations', {}).get(lang_code)
    elif context.location == TranslationContextLocation.command_description:
      return command_data.get('description_localizations', {}).get(lang_code)
    elif context.location == TranslationContextLocation.parameter_name:
      param_name = string.message if hasattr(string, 'message') else str(string)
      for opt in command_data.get('options', []):
        if opt['name'] == param_name:
          return opt.get('name_localizations', {}).get(lang_code)
      return None
    return None