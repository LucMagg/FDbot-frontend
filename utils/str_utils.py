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
  if input_string is None:
    return None
  else:
    if type(input_string) is str:
      slug = input_string.replace(' ','_').replace('&','%26')
      return slug
    else:
      return None