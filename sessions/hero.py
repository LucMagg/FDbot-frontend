from datetime import datetime
from collections import defaultdict

from ui.base_ui import BaseUiData
from states.hero import HeroState

from utils.str_utils import str_to_slug, format_float
from utils.misc_utils import stars, rank_text


class HeroSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))
    self.state = HeroState()
    self.error_msg = self.bot.message.get_message('error').get(self.ui.langcode)
    self.return_msg = self.bot.message.get_message('hero').get(self.ui.langcode)
    self.nocomment_msg = self.bot.message.get_message('nocomment').get(self.ui.langcode)

    self.state.hero = cog_data.get('hero')
    self.gear_items = [
      {'to_find': 'A0', 'text': 'base'},
      {'to_find' : 'A1', 'text': 'ascend'},
      {'to_find' : 'A2', 'text': 'ascend'},
      {'to_find' : 'A3', 'text': 'ascend'},
      {'to_find' : 'A4', 'text': 'ascend'}
    ]
    self.gear_positions = ['Amulet', 'Weapon', 'Ring', 'Head', 'Off-Hand', 'Body']

  # Session entry point
  async def start(self):
    try:
      self.ui.wait_message = True
      await self.ui.send()
      await self.ui.clear()
      self.ui.response = await self._get_response()
      await self.ui.send()
    except Exception as e:
      self.logger.session_exception('Hero', e)

  # Get command response
  async def _get_response(self) -> dict:
    if str_to_slug(self.state.hero) == self._translate('help'):
      return self.bot.message.get_help(whichone='hero', lang=self.ui.langcode)
    self.state.hero_dict = await self.bot.back_requests.call('getHeroByName', [self.state.hero])
    if 'error' in self.state.hero_dict:
      return self._return_error(error='not found')
    if self.state.hero_dict.get('pet'):
      self.state.pet_dict = await self.bot.back_requests.call('getPetByName', [self.state.hero_dict.get('pet')])
      if 'error' in self.state.pet_dict:
        return self._return_error(error='request error')
      active_talent = next((t for t in self.state.pet_dict.get('talents') if t.get('position') == 'gold'), None)
      self.state.pet_active_talent = await self.bot.back_requests.call('getTalentByName', [active_talent.get('name')]) if active_talent else None
    else:
      self.state.pet_dict = None
    return {
      'description': self._build_description(),
      'fields': self._build_fields(),
      'color': self.state.hero_dict.get('color'),
      'thumbnail': self.state.hero_dict.get('image_url')
    }
  
  # Error builder
  def _return_error(self, error: str) -> dict:
    description = f'## {self.error_msg.get('title')} ##\n'
    match error:
      case 'not found':
        self.logger.log('debug', f'[HERO] Argument not found in DB : {self.state.hero}')
        description += f'{self.error_msg.get('part1')}{self.state.hero}{self.error_msg.get('part2')}'
      case 'request error':
        self.logger.log('error', f'[HERO] Error while requesting backend')
        description += self.error_msg.get('generic')
    return {'description': description, 'color': self.bot.message.get_message('error').get('color')}
  
  # Description builder
  def _build_description(self) -> str:
    return (
      self._display_header() +
      self._display_stats() + '\n' +
      self._display_ascend_gain() + '\n' +
      self._display_lead()
    )
  
  # Fields builder
  def _build_fields(self) -> list:
    result = (
      [self._empty_field()] +
      self._fields_talents() +
      self._fields_gear() +
      [self._empty_field()]
    )
    if self.state.hero_dict.get('pet'):
      result.append(self._field_pet())
      result.append(self._empty_field())
    comments = self._fields_comments()
    for c in comments:
      result.append(c)
    return result
  
  # Description helpers
  #    Header
  def _display_header(self) -> str:	
    result = (
      f'# {self._translate(self.state.hero_dict.get('name'))}'
      f'    {stars(self.state.hero_dict.get('stars'))} #\n'
    )
    if 'exclusive' in self.state.hero_dict.keys() and self.state.hero_dict.get('exclusive'):
      result += (
        f'## {self._translate(self.state.hero_dict.get('exclusive'))} '
        f'{self._translate('Exclusive')} ##\n'
      )
    result += (
      f'{self._translate(f'{self.state.hero_dict.get('color')} {self.state.hero_dict.get('species')} S')}'
      f' {self._translate(f'{self.state.hero_dict.get('heroclass')} S').lower()}\n\n'
    )
    return result

  #    Stats
  def _display_stats(self) -> str:
    result = (
      f'__**{self.return_msg.get('stats')} ({self.state.hero_dict.get('ascend_max')} - '
      f'{self.return_msg.get('level')} {self.state.hero_dict.get('lvl_max')})**__\n'
    )
    for attribute in ['Attack', 'Defense']:
      result += self._display_stat_cap(attribute) + self._display_stat_rank(attribute)
    return result
  
  #      stat cap
  def _display_stat_cap(self, attribute: str) -> str:
    data = self.state.hero_dict.get(f'{attribute.lower()}_max').get(self.state.hero_dict.get('ascend_max'))
    result = (
      f'**{self._translate(attribute)}**\n'
      f'{self.return_msg.get('total')} : {data.get('total')}\n'
      f'_({self.return_msg.get('base')} : {data.get('base')} + '
      f'{self.return_msg.get('gear')} : {data.get('gear')} + '
      f'{self.return_msg.get('merge')} : {data.get('merge')}'
    )
    if data.get('pet', None) is not None:
      result += f' + {self.return_msg.get('pet')} : {data.get('pet')}'
    return result
  
  #      stat rank
  def _display_stat_rank(self, attribute: str) -> str:
    attr = attribute[:3].lower()
    return (
      f')\n{self.state.hero_dict.get(f'{attr}_rank')}'
      f'{self._translate(rank_text(self.state.hero_dict.get(f'{attr}_rank')))} '
      f'{self.return_msg.get('out of')} {self.state.hero_dict.get('class_count')} '
      f'{str.lower(self._translate(f'{self.state.hero_dict.get('heroclass')} P'))} '
      f'({self.return_msg.get('class average')} : {self.state.hero_dict.get(f'{attr}_average')})_\n'
    )
  
  #    Ascend gain
    #    Ascend gain
  def _display_ascend_gain(self) -> list:
    attack_max  = self.state.hero_dict.get('attack_max')
    defense_max = self.state.hero_dict.get('defense_max')
    available   = list(attack_max.keys())
    if len(available) < 2:
      return []
    result = f'__**{self.return_msg.get('ascend_gain')}**__\n'
    for i in range(1, len(available)):
      prev, curr = available[i - 1], available[i]
      att_prev = attack_max[prev]['total']
      att_curr = attack_max[curr]['total']
      def_prev = defense_max[prev]['total']
      def_curr = defense_max[curr]['total']
      att_gain = att_curr - att_prev
      def_gain = def_curr - def_prev
      att_pct = format_float(att_gain / att_prev * 100)
      def_pct = format_float(def_gain / def_prev * 100)
      result += (
        f'**{prev} → {curr}** - '
        f'{self._translate('Attack')} : +{att_gain} _(+{att_pct}%)_ | '
        f'{self._translate('Defense')} : +{def_gain} _(+{def_pct}%)_\n'
      )
    return result
    
  #    Lead
  def _display_lead(self) -> str:
    result = f'__**{self.return_msg.get('lead bonus')}**__\n'
    for l in ['lead_color', 'lead_species']:
      lead = self.state.hero_dict.get(l)
      lead_result = self._display_lead_first_part(lead)
      result += f'{self._display_lead_second_part(lead, lead_result)}\n'
    result += '\n'
    return result
  
  #      lead first part (att/def boost or talent)
  def _display_lead_first_part(self, lead: dict) -> str:
    result = ''
    if lead.get('attack'):
      if lead.get('defense'):
        if lead.get('attack') == lead.get('defense'):
          result = f'{lead.get('attack'):.2f} {self.return_msg.get('att/def')}'
        else:
          result = (
            f'{lead.get('attack'):.2f} {self.return_msg.get('att')} '
            f'{self.return_msg.get('and')} '
            f'{lead.get('defense'):.2f} {self.return_msg.get('def')}'
          )
      else:
        result = f'{lead.get('attack'):.2f} {self.return_msg.get('att')}'
    else:
      if lead.get('defense'):
        result = f'{lead.get('defense'):.2f} {self.return_msg.get('def')}'
      if lead.get('talent'):
        result = f'{self._translate(lead.get('talent'))}'
    return result

  #      lead second part (color, species and extra)
  def _display_lead_second_part(self, lead: dict, result: str) -> str:
    if result == '':
      return ''
    result += f' {self.return_msg.get('for')} '
    if lead.get('color'):
      if lead.get('species'):
        result += f'{self._translate(f'{lead.get('color')} {lead.get('species')} P')}'
      else:
        result += f'{self._translate(f'{lead.get('color')} P')}'
    elif lead.get('species'):
      result += f'{self._translate(f'{lead.get('species')} P')}'
    if lead.get('extra'):
      result += (
        f' {self.return_msg.get('or')} '
        f'{self._translate(lead.get('extra'))}'
      )
    return result

  # Fields helpers
  #    Talents
  def _fields_talents(self) -> list:
    talents = defaultdict(list)
    for t in self.state.hero_dict.get('talents'):
      parts = t.get('position', '').split()
      kind, idx = parts[0], int(parts[1])
      talents[kind].append((idx, t.get('name')))
    fields = [{'name': f'__**{self.return_msg.get('talents')}**__', 'value': '', 'inline': False}]
    fields += self._fields_grouped_talents(talents)
    fields += self._fields_unique_talents()
    return fields
  
  #      base / ascend / merge talents
  def _fields_grouped_talents(self, talents: dict) -> list:
    talents_by_type = {kind: [name for i, name in sorted(values)] for kind, values in talents.items()}
    fields = []
    for kind in ('base', 'ascend', 'merge'):
      talent_list = talents_by_type.get(kind)
      if not talent_list:
        continue
      value = '\n'.join([self._translate(t) for t in talent_list if t])
      fields.append({
        'name': f'**{self.return_msg.get(kind).capitalize()}**',
        'value': value,
        'inline': True
      })
    return fields
  
  #      unique talents
  def _fields_unique_talents(self) -> list:
    unique = self.state.hero_dict.get('unique_talents', [])
    if unique:
      whichone = f'unique talent{'s' if len(unique) > 1 else ''}'
      return [{
        'name': (
          f'**{self.return_msg.get(whichone)} {self.return_msg.get('amongst all')} '
          f'{self._translate(f'{self.state.hero_dict.get('heroclass')} P').lower()}**'
        ),
        'value': f'{'\n'.join([self._translate(ut) for ut in unique if ut])}',
        'inline': False
      }, self._empty_field()]
    return [self._empty_field()]

  #    Gear
  def _fields_gear(self) -> list:
    fields = [{'name': f'__**{self.return_msg.get('gears')}**__', 'value': '', 'inline': False}]
    has_an_ascend = [True if self.state.hero_dict.get('attack').get(i.get('to_find')) else False for i in self.gear_items]
    for index, item in enumerate(self.gear_items):
      if not has_an_ascend[index]:
        break
      str_index = ''
      if index > 0:
        str_index = f'{str(index)}{self._translate(rank_text(index))} '

      price = 0
      gear_text = ''
      for pos in self.gear_positions:
        gear = next((g for g in self.state.hero_dict.get('gear') if g.get('ascend') == item.get('to_find') and g.get('position') == pos), None)
        if gear:
          quality = next((q for q in self.bot.static_data.qualities if q['name']['en'] == gear['quality']), None)
          if quality:
            gear_text += f'{quality.get('icon')} {self._translate(f'{gear.get('quality')} {gear.get('name')}')}\n'
            price += quality.get('price')

      fields.append({
        'name': f'**{str_index}{self.return_msg.get(item.get('text')).capitalize()}** ({price} :gem:)',
        'value': gear_text or '\u200b',
        'inline': True
      })
      if index % 2 == 1 and index + 1 < len(has_an_ascend) and has_an_ascend[index + 1]:
        fields.append(self._empty_field())
    return fields
  
  #    Pet
  def _field_pet(self) -> list:
    if not self.state.hero_dict.get('pet'):
      return []
    value = f'{self.return_msg.get('max att/def bonus')} : {self.state.pet_dict.get('attack')}%\n'      
    passive_talent = next((t for t in self.state.pet_dict.get('talents') if t.get('position') == 'full'), None)
    if passive_talent and passive_talent.get('name'):
      value += (
        f'{self.return_msg.get('passive talent')} '
        f'{self._translate(f'{self.state.hero_dict.get('heroclass')} P').lower()} : '
        f'{self._translate(passive_talent.get('name'))}\n'
      )
    active_talent = next((t for t in self.state.pet_dict.get('talents') if t.get('position') == 'gold'), None)
    if active_talent:
      value += (
        f'{self.return_msg.get('active talent')} '
        f'{self._translate(self.state.hero_dict.get('name'))} : '
        f'{self._translate(active_talent.get('name'))}\n'
      )
      if 'error' not in self.state.pet_active_talent:
        value += f' -> {self.state.pet_active_talent.get('description')}\n'
    return {
      'name': f'__**{self.return_msg.get('signature pet')} : {self._translate(self.state.pet_dict.get('name'))}**__\n',
      'value': f'{value}\n',
      'inline': False
    }  

  #    Comments
  def _fields_comments(self) -> list:
    comments = [c for c in self.state.hero_dict.get('comments') if c.get('lang') == self.ui.langcode]
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
  def _translate(self, key) -> str:
    return self.bot.language.translate_from_key(text_to_translate=key, lang=self.ui.langcode)
  
  #    Empty field
  def _empty_field(self) -> dict:
    return {'name': '\u200b', 'value': '\u200b', 'inline': False}