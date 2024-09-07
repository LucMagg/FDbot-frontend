from time import strftime, localtime
import re

def str_now():
	"""renvoie la date et l'heure sous forme de chaîne"""

	return strftime('%Y-%m-%d %H:%M:%S', localtime())

def str_to_slug(input_string: str|None) -> str|None:
  if input_string is None:
    return None
  else:
    if type(input_string) is str:
      slug = input_string.lower()

      special_chars = {':': r'\:', '\and': r'\and', '&': r'\and', '-': r'\-'}
      for char, escaped in special_chars.items():
          slug = slug.replace(char, escaped)

      slug = slug.replace(' ', '-')
      slug = re.sub(r'[^a-z0-9\-\:\&]', '', slug)
      slug = re.sub(r'-+', '-', slug)
      slug = slug.strip('-')
    else:
      slug = input_string
    
    return slug
  
def slug_to_str(slug: str|None) -> str|None:
  if slug is None:
    return None
  else:
    if type(slug) is str:
      special_chars = {r'\:': ':', r'\and': '&', r'\-': '-'}
      for escaped, char in special_chars.items():
        slug = slug.replace(escaped, char)

      original_string = slug.replace('-', ' ')
      
      words = original_string.split()
      capitalized_words = [word.capitalize() if word not in ['of', 'to'] else word for word in words]
      original_string = ' '.join(capitalized_words)

    else:
      original_string = slug

    return original_string
  
def str_to_wiki_url(input_string: str|None) -> str|None:
  if input_string is None:
    return None
  else:
    if type(input_string) is str:
      slug = input_string.replace(' ','_').replace('&','%26')
      return slug
    else:
      return None