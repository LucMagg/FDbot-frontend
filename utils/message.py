class Message:
  def __init__(self, bot):
    self.bot = bot

  def message(self, whichone):
    messages = self.bot.static_data.get_messages()
    return next((m for m in messages if m['name'] == whichone), None)
  
  def help(self, whichone, options = ''):
    help_messages = Message.message(self, 'help')

    if whichone == 'help':  
      return {'title': help_messages['title']['generic'], 'description': help_messages['description']['generic'], 'color': help_messages['color']}
    
    title = f"{help_messages['title']['command']}{whichone}"
    description = f"{help_messages['description'][whichone]}{options}"
    return {'title': title, 'description': description, 'color': help_messages['color']}