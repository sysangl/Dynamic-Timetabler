import toml
from pathlib import Path

class Config():
    config = {}

    @classmethod
    def load_config(cls, config_path: str | None = None):
        #if not config_path:
        config_path = (Path.home() / '.dynamic-timetabler' / 'testing.toml').as_posix()
        with open(config_path, 'r') as f:
            cls.config = toml.load(f)
        print(cls.config)
        return cls.config