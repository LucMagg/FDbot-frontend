from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from sessions.level import LevelSession

class MercCommon:
  # Display merc details
  def display_merc_details(merc: dict, return_msg: list[str]) -> str:
    details = []
    if merc.get('ascend'):
      details.append(merc.get('ascend'))
    if merc.get('merge'):
      details.append(f'M{merc.get('merge')}')
    has_talent = False
    for talent_key in ('a4_talent', 'a3_talent', 'a2_talent'):
      if merc.get(talent_key):
        has_talent = True
        details.append(f'{return_msg.get('with')} {return_msg.get(talent_key.replace('_', ' '))}')
        break
    if merc.get('pet'):
      link = 'and' if has_talent else 'with'
      details.append(f'{return_msg.get(link)} {return_msg.get('pet')}')
      if merc.get('pet_talent'):
        details.append(return_msg.get('pet talent'))
    return f'({' '.join(details)})' if details else ''

  # Display mercs by color
  def display_mercs_by_color(session: LevelSession) -> str:
    mercs_by_color = MercCommon._sort_mercs_by_color(session)
    result = []
    current_color = None
    for i, merc in enumerate(mercs_by_color):
      color = merc.get('color')
      if color != current_color:
        next_color = None
        if i + 1 < len(mercs_by_color):
          next_color = mercs_by_color[i + 1].get('color')
        color_suffix = 'P' if next_color == color else 'S'
        result.append(f'\n### {session._translate(f'{color} {color_suffix}')} ###')
        current_color = color
      result.append(f'- {session._translate(merc.get('name'))} {MercCommon.display_merc_details(merc, session.return_msg)}')
    return result

  # Sort mercs by color helper
  def _sort_mercs_by_color(session) -> dict:
    heroes_by_slug = {h['name_slug']: h for h in session.state.heroes}
    result = []
    for m in session.state.merc_list.get('mercs'):
      hero = heroes_by_slug.get(m.get('name_slug'))
      result.append({**m, 'color': hero.get('color')})
    return sorted(result, key=lambda m: (m.get('color'), m.get('name')))