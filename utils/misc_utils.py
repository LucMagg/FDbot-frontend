import discord
from typing import Union, List


def get_discord_color(color: str):
	"""renvoie la couleur Discord en fonction de color"""
	match str.lower(color):
		case 'default':
			return discord.Color.default()
		case 'red':
			return discord.Color.red()
		case 'green':
			return discord.Color.green()
		case 'blue':
			return discord.Color.blue()
		case 'light':
			return discord.Color.gold()
		case 'dark':
			return discord.Color.magenta()


def stars(how_many):
	stars = ''
	for iter in range(0, how_many):
		stars += ':star:'
	return stars

def rank_text(number):
	if number == 1:
		return 'er'
	else:
		return 'ème'
	
def pluriel(elements: Union[List, int]) -> str:
	if isinstance(elements, int):
		if elements > 1:
			return 's'
		else:
			return ''
	if len(elements) > 1:
		return 's'
	return ''

def nick(message: discord.message) -> str:
	nickname = message.user.nick
	if nickname is None:
		nickname = message.user.global_name
	return nickname

def convert_seconds(seconds) -> str:
	to_return = []
	hours = seconds // 3600
	if hours > 0:
		seconds = seconds % 3600
		to_return.append(f'{hours} heures')
	minutes = seconds // 60
	if minutes > 0:
		seconds = seconds % 60
		to_return.append(f'{minutes} minutes')
	if seconds > 0:
		to_return.append(f'{seconds} secondes')
	return ', '.join(to_return)