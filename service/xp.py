import math


class XpService:
  ascends = ["A0", "A1", "A2", "A3"]

  @staticmethod
  def calc_xp(xp_table, threshold_table, stars, start_ascend, start_level, target_ascend, target_level):
    initial_return = f' potions d\'xp pour passer un héros {stars}* de {start_ascend} niveau {start_level} à {target_ascend} niveau {target_level}'

    current_ascend_potions = 0
    total_potions = 0

    current_level = start_level
    current_ascend = start_ascend
    current_ascend_idx = XpService.ascends.index(current_ascend)

    calc_return = ''
    threshold = threshold_table.get(current_ascend).get('threshold')

    if threshold is not None:
      if current_level >= threshold:
        current_level = math.ceil(current_level / 2)
        current_ascend_idx += 1
        current_ascend = XpService.ascends[current_ascend_idx]
        calc_return = f'- passer directement {current_ascend}\n'

    while not current_level == target_level or not current_ascend == target_ascend:
      current_level += 1
      level_potions = next((xp.get(current_ascend) for xp in xp_table if xp.get('level') == current_level), None)
      if level_potions is not None:
        current_ascend_potions += level_potions

      if current_ascend != target_ascend:
        if current_level == threshold:
          calc_return += f'- utiliser {current_ascend_potions} potions d\'xp jusqu\'à {current_ascend} niveau {current_level}\n'
          current_level = math.ceil(current_level / 2)
          current_ascend_idx += 1
          current_ascend = XpService.ascends[current_ascend_idx]
          threshold = threshold_table.get(current_ascend).get('threshold')
          calc_return += f'- ascend {current_ascend}\n'
          total_potions += current_ascend_potions
          current_ascend_potions = 0
    total_potions += current_ascend_potions

    if calc_return != '' and total_potions != 0:
      calc_return += f'- utiliser {current_ascend_potions} potions d\'xp jusqu\'à {current_ascend} niveau {current_level}\n'
      optional_return = ', en suivant ce cheminement :\n'
    else:
      optional_return = '.'

    return f'Il faut {total_potions}{initial_return}{optional_return}{calc_return}'

  @staticmethod
  def check_errors(threshold_table, stars, start_ascend, start_level, target_ascend, target_level):
    start_error = XpService.check_input_error(threshold_table, stars, start_ascend, start_level)
    if start_error:
      return start_error

    target_error = XpService.check_input_error(threshold_table, stars, target_ascend, target_level)
    if target_error:
      return target_error

    if start_ascend == target_ascend and start_level == target_level:
      return {'title': 'Requête stupide :wink:',
              'description': 'Pour garder le même level, le héros n\'a pas besoin de potions d\'xp :shrug:',
              'color': 'red'}

    if int(start_ascend[1]) > int(target_ascend[1]):
      return {'title': 'Erreur',
              'description': 'Il n\'est pas possible pour un héros de baisser son niveau d\'ascension :shrug:',
              'color': 'red'}

    if start_ascend == target_ascend and start_level > target_level:
      return {'title': 'Erreur', 'description': 'Il n\'est pas possible pour un héros de baisser de niveau :shrug:',
              'color': 'red'}

    if int(start_ascend[1]) + 1 == int(target_ascend[1]) and math.ceil(start_level / 2) > target_level:
      description = f'Il n\'est pas possible pour un héros de passer de {start_ascend} niveau {start_level} à {target_ascend} niveau {target_level}, étant donné qu\'après ascension il sera déjà '
      return {
        'title': 'Requête stupide :wink:',
        'description': f'{description} {start_ascend} niveau {start_level} :shrug:',
        'color': 'red'
      }

    return None

  @staticmethod
  def check_input_error(threshold_table, stars, ascend, level):
    threshold_data = threshold_table.get(ascend)
    if level < threshold_data.get('level').get('min') or level > threshold_data.get('level').get('max'):
      return {
        'title': 'Erreur',
        'description': f'Il est impossible pour un héros {stars}* d\'être level {level} avec une ascension {ascend}.\nMerci de vérifier et de réitérer la commande :rolling_eyes:',
        'color': 'red'
      }

    return None
