import os
from datetime import datetime, timezone, timedelta

dc_folder = os.path.join('images', 'dc')

class DcCleanerSession:
  def __init__(self, data: dict):
    self.bot = data.get('bot')
    self.logger = self.bot.logger

  # Session entry point
  async def start(self):
    try:
      date = datetime.now(tz=timezone.utc)
      days = date.day
      delta = date + timedelta(days=1)
      self.logger.log_only('info', f'[LOOP] DC cleaner loop triggered {date} | days: {days}')
      if delta.day == 1:
        self.logger.bot_log(f'[LOOP] DC cleaner loop : delete all previous DC entries')
        result = await self.bot.back_requests.call('clearDC')
        if result:
          self.logger.bot_log(f'[LOOP] DC cleaner loop : {result.get('message')}')
        for filename in os.listdir(dc_folder):
          file_path = os.path.join(dc_folder, filename)
          if os.path.isfile(file_path):
            os.remove(file_path)
    except Exception as e:
      self.logger.log_only('error', f'[LOOP] DC cleaner loop error : {e}')