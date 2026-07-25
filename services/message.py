class MessageService:
  def __init__(self, bot):
    self.bot = bot
    self.messages = self.bot.static_data.get_messages()

  def get_message(self, whichone):
    return next((m for m in self.messages if m.get('name') == whichone), None)
  
  def get_help(self, whichone, lang = 'en', options = ''):
    help_msg = self.get_message('help').get(lang)

    if whichone == 'help':
      description = f'## {help_msg.get('title').get('generic')} ##\n{help_msg.get('description').get('generic')}'
      return {'description': description, 'color': self.get_message('help').get('color')}
    
    description = f'## {help_msg.get('title').get('command')}{whichone} ##\n{help_msg.get('description').get(whichone)}{options}'
    return {'description': description, 'color': self.get_message('help').get('color')}