from time import strftime, localtime
import re

def str_now():
	"""renvoie la date et l'heure sous forme de chaîne"""

	return strftime('%Y-%m-%d %H:%M:%S', localtime())

def str_to_slug(input_string: str|None) -> str|None:
  if input_string is None or not isinstance(input_string, str):
    return None
  
  if re.match(r'^[a-z0-9\-\:\&\\_]+$', input_string):
    return input_string

  to_return = input_string.lower()

  special_chars = {':': r'\:', '\and': r'\and', '&': r'\and', '-': r'_'}
  for char, escaped in special_chars.items():
    to_return = to_return.replace(char, escaped)

  to_return = to_return.replace(' ', '-')
  to_return = re.sub(r'[^a-z0-9\-\:\&\\\_]', '', to_return)
  to_return = re.sub(r'-+', '-', to_return)
  to_return = to_return.strip('-')
  return to_return
  
def slug_to_str(slug: str|None) -> str|None:
  if slug is None or not isinstance(slug, str):
    return None
  
  if re.match(r'^[a-z\\:]+(?:[-_][a-z\\:]+)*$', slug):
    return slug

  def capitalize_words(text):
    words = text.split()
    return ' '.join(word.capitalize() if word.lower() not in ['of', 'Of', 'to', 'and'] else word for word in words)

  parts = slug.split('_')
  capitalized_parts = [capitalize_words(part.replace('-', ' ')) for part in parts]
  to_return = '_'.join(capitalized_parts)

  special_chars = {r'\:': ':', r'\and': '&', '_': '-'}
  for escaped, char in special_chars.items():
    to_return = to_return.replace(escaped, char)
  
  return to_return
  
def str_to_wiki_url(input_string: str|None) -> str|None:
  if input_string is None or not isinstance(input_string, str):
    return None

  to_return = input_string.replace(' ','_').replace('&','%26')
  return to_return
    
def str_to_int(input_string):
  if input_string is None:
    return None
  
  if isinstance(input_string, int):
    return input_string
  
  try:
    input_int = int(input_string)
    print(input_int)
  except Exception as e:
    print(f'error: {e}')
    if input_string[-1].lower() == 'k':
      try:
        input_int = int(input_string[:-1]) * 1000
      except Exception as e:
        print(f'error: {e}')
        return None
      
  return input_int

def int_to_str(input_int):
  if input_int is None:
    return None
  
  if not isinstance(input_int, int):
    return input_int
  
  if input_int < 1000:
    return input_int

  if input_int % 1000 == 0:
    return f'{input_int//1000}k'
  
  return f'{input_int/1000}k'