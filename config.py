import toml

class Config():
    config = {}

    @classmethod
    def load_config(cls, config_path: str = 'config/default.toml'):
        with open(config_path, 'r') as f:
            cls.config = toml.load(f)
        print(cls.config)
        return cls.config