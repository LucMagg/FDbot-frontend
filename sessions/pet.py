from typing import Dict
from datetime import datetime

from ui.base_ui import BaseUiData
from states.pet import PetState

from utils.str_utils import str_to_slug
from utils.misc_utils import stars


class PetSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = PetState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('pet').get(self.ui.langcode)
    self.nocomment_msg = self.bot.message.get_message('nocomment').get(self.ui.langcode)

    self.state.pet = cog_data.get('pet')

  # Session entry point
  async def start(self):
    try:
      self.ui.wait_message = True
      await self.ui.send()
      await self.ui.clear()
      self.ui.response = await self._get_response()
      await self.ui.send()
    except Exception as e:
      self.logger.session_exception('Pet', e)

  # Get command response
  async def _get_response(self) -> Dict:
    if str_to_slug(self.state.pet) == self._translate('help'):
      return self.bot.message.get_help(whichone='pet', lang=self.ui.langcode)
    self.state.pet_dict = await self.bot.back_requests.call('getPetByName', [self.state.pet])
    if 'error' in self.state.pet_dict:
      return self._return_error(error='not found')
    self.state.heroes_by_pet = await self.bot.back_requests.call('getHeroesByPet', [self.state.pet])
    active_talent = next((t for t in self.state.pet_dict.get('talents') if t.get('position') == 'gold'), None)
    self.state.active_talent = await self.bot.back_requests.call('getTalentByName', [active_talent.get('name')]) if active_talent else None
    return {
      'description': self._build_description(),
      'fields': self._build_fields(),
      'color': self.state.pet_dict.get('color'),
      'thumbnail': self.state.pet_dict.get('image_url')
    }
  
  # Error builder
  def _return_error(self, error: str) -> Dict:
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'not found':
        self.logger.log('debug', f'[PET] Argument not found in DB : {self.state.pet}')
        description += f'{self.error_msg.get('part1')}{self.state.hero}{self.error_msg.get('part2')}'
    return {'description': description, 'color': self.bot.message.get_message('error').get('color')}
  
  # Description builder
  def _build_description(self) -> str:   
    return (
      self._display_header() +
      self._display_stats() +
      self._display_signature() +
      self._display_other_heroes()
    )
  
  # Fields builder
  def _build_fields(self) -> list:
    return (
      [self._empty_field()] +
      self._fields_talents() +
      [self._empty_field()] +
      self._fields_comments()
    )
   
  # Description helpers
  #    Header
  def _display_header(self) -> str:
    result = f'# {self._translate(self.state.pet_dict.get('name'))}    {stars(self.state.pet_dict.get('stars'))} #\n'
    if 'exclusive' in self.state.pet_dict.keys() and self.state.pet_dict.get('exclusive'):
      result += f'## {self._translate(self.state.pet_dict.get('exclusive'))} {self._translate('Exclusive')} ##\n'
    result += f'{self._translate(f'{self.state.pet_dict.get('color')} {self.state.pet_dict.get('petclass')}').capitalize()}\n\n'
    return result
  
  #    Stats
  def _display_stats(self) -> str:
    result = (
      f'__**{self.return_msg.get('stats')}**__\n'
      f'\u00A0\u00A0+ {self.state.pet_dict.get('attack')}% {self.return_msg.get('att/def')}\n'
    )
    return result
  
  #    Signature hero(es)
  def _display_signature(self) -> str:
    recolor_signature = bool(self.state.pet_dict.get('signature_bis'))
    result = (
      f'__**{self.return_msg.get(f'signature hero{'es' if recolor_signature else ''}')}**__\n'
      f'\u00A0\u00A0{self._translate(self.state.pet_dict.get('signature'))}'
      f'{f' | {self._translate(self.state.pet_dict.get('signature_bis'))}' if recolor_signature else ''}'
      f'\n'
    )
    return result

  #    Other hero(es)
  def _display_other_heroes(self) -> str:
    if 'error' in self.state.heroes_by_pet:
      return ''
    has_passive = next((t.get('name') for t in self.state.pet_dict.get('talents') if t.get('position') == 'full'), None)
    if not has_passive:
      return ''
    heroes = [h.get('name') for h in self.state.heroes_by_pet if h.get('name') != self.state.pet_dict.get('signature')]
    result =  f'__**{self.return_msg.get(f'passive talent hero{'es' if len(heroes) > 1 else ''}')}**__\n\u00A0\u00A0{', '.join([self._translate(h) for h in heroes])}'
    return result
  
  #    Talents
  def _fields_talents(self) -> str:
    talents_by_pos = {t.get('position'): t.get('name') for t in self.state.pet_dict.get('talents')}
    fields = [{'name': f'__**{self.return_msg.get('talents')}**__', 'value': '', 'inline': False}]
    fields += (
      self._fields_base_and_silver(talents_by_pos) +
      self._field_merge_talents()
    )
    if talents_by_pos.get('full'):
      fields += self._field_passive_talent(talents_by_pos)
    fields += self._field_active_talent(talents_by_pos)
    return fields
  
  #      base & silver
  def _fields_base_and_silver(self, talents_by_pos: list[Dict]) -> list:
    fields = [
      {
        'name': f'**{self.return_msg.get('base')}**',
        'value': f'{talents_by_pos.get('base')} {self.return_msg.get('1att/def')}',
        'inline': True
      },
      {
        'name': f'**{self.return_msg.get('silver')}**',
        'value': f'{talents_by_pos.get('silver')} {self.return_msg.get('2att/def')}',
        'inline': True
      }
    ]
    return fields
  
  #      merge
  def _field_merge_talents(self) -> list:
    merge_talents = sorted([t for t in self.state.pet_dict.get('talents') if 'merge' in t.get('position')], key=lambda x:int(x.get('position').split(' ')[1]))
    field = [{
      'name': f'**{self.return_msg.get('merge')}**',
      'value': ' | '.join([self._translate(m.get('name')) for m in merge_talents]),
      'inline': False
    }]
    return field
    
  #      passive
  def _field_passive_talent(self, talents_by_pos: list[Dict]) -> list:
    field = [{
      'name': f'**{self.return_msg.get('passive')}**',
      'value': f'{self._translate(talents_by_pos.get('full'))} ({self.return_msg.get('only for')} {self._translate(f'{self.state.pet_dict.get('petclass')} P')})',
      'inline': False
    }]
    return field
  
  #      active
  def _field_active_talent(self, talents_by_pos: list[Dict]) -> list:
    value = f'{self._translate(talents_by_pos.get('gold'))}'
    if 'error' not in self.state.active_talent:
      value += f' : {self.state.active_talent.get('description')}'
    manacost_merge = sum(1 for t in self.state.pet_dict.get('talents') if t.get('name') == 'Mana Efficiency')
    value += (
      f'\n**{self.return_msg.get('mana cost')}** 25 ({self.return_msg.get('base').split(':')[0].strip().lower()}) - '
      f'{25 - self.state.pet_dict.get('manacost') - manacost_merge} ({self.return_msg.get('active').split(':')[0].strip().lower()})'
     )
    if manacost_merge > 0:
      value += f' - {manacost_merge} ({self.return_msg.get('merge').split(':')[0].strip().lower()})'
    value += f' = **{self.state.pet_dict.get('manacost')}**\n'   
    field = [{
      'name': f'**{self.return_msg.get('active')}**',
      'value': value,
      'inline': False
    }]
    return field

  #    Comments
  def _fields_comments(self) -> list:
    comments = [c for c in self.state.pet_dict.get('comments') if c.get('lang') == self.ui.langcode]
    whichone = f'comment{'s' if len(comments) > 1 else ''}'
    name = f'__**{self.return_msg.get(whichone)}**__\n'
    if not comments:
      return [{
        'name': name,
        'value': self.nocomment_msg,
        'inline': False
      }]
    fields = [{'name': name, 'value': '', 'inline': False}]
    for comment in comments:
      my_date = datetime.strptime(comment.get('date'), '%a, %d %b %Y %H:%M:%S %Z').strftime(self.return_msg.get('date_format'))
      fields.append({
        'name': f'__{comment.get('author')} {self.return_msg.get('on')} {my_date}__\n',
        'value': comment.get('commentaire'),
        'inline': False
      })
    return fields
  
  #    Translate
  def _translate(self, key: str) -> str:
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)
  
  #    Empty field
  def _empty_field(self) -> dict:
    return {'name': '\u200b', 'value': '\u200b', 'inline': False}  