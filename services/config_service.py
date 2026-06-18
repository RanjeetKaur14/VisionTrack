import json


class ConfigService:

    @staticmethod
    def load():

        with open(
            "config/config.json",
            "r"
        ) as f:

            return json.load(f)