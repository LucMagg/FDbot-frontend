from dataclasses import dataclass, field


@dataclass(slots=True)
class DcState():
  level: str = None
  screenshots: list = field(default_factory=list)
  replay: str = None
  screenshots_filepath: list = field(default_factory=list)
  dc_level: dict = field(default_factory=dict)

  def to_dict(self):
    return {
      'name': self.level,
      'screenshots': self.screenshots_filepath,
      'replays': [self.replay]
    }