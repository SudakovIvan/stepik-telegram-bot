import pytrivia
import json


class SettingsToJsonSaver:
    def __init__(self, file_name):
        self._file_name = file_name

    def load(self):
        return json.load(open(self._file_name, "r"))

    def dump(self, settings):
        json.dump(settings, open(self._file_name, "w"))


class DefaultSaver:
    def load(self):
        return {}

    def dump(self, settings):
        pass


class SettingsManager:

    DEFAULT_SETTINGS = {"question_count": "3",
                        "difficulty": "easy",
                        "category": "18"
                        }

    def __init__(self, settings_saver):
        self._settings_saver = settings_saver
        try:
            self._settings = self._settings_saver.load()
        except Exception as ex:
            print(ex)
            self._settings = {}

    def save_question_count(self, user_id, count):
        self._save_parameter(user_id, "question_count", count)

    def save_difficulty(self, user_id, difficulty):
        self._save_parameter(user_id, "difficulty", difficulty)

    def save_category(self, user_id, category):
        self._save_parameter(user_id, "category", category)

    def get_question_count(self, user_id):
        try:
            current_settings = self._get_current_settings(user_id)
            result = int(current_settings.get("question_count", self.DEFAULT_SETTINGS["question_count"]))
        except Exception as ex:
            print(ex)
            result = int(self.DEFAULT_SETTINGS["question_count"])
        return result

    def get_difficulty(self, user_id):
        current_settings = self._get_current_settings(user_id)
        data = current_settings.get("difficulty", self.DEFAULT_SETTINGS["difficulty"])

        if data == "easy":
            result = pytrivia.Diffculty.Easy
        elif data == "medium":
            result = pytrivia.Diffculty.Medium
        elif data == "hard":
            result = pytrivia.Diffculty.Hard
        else:
            result = pytrivia.Diffculty(self.DEFAULT_SETTINGS["difficulty"])

        return result

    def get_category(self, user_id):
        current_settings = self._get_current_settings(user_id)
        data = current_settings.get("category", self.DEFAULT_SETTINGS["category"])
        try:
            result = pytrivia.Category(int(data))
        except Exception as ex:
            print(ex)
            result = pytrivia.Category(int(self.DEFAULT_SETTINGS["category"]))

        return result

    def _get_current_settings(self, user_id):
        user_id_str = str(user_id)
        if user_id_str not in self._settings:
            self._settings[user_id_str] = self.DEFAULT_SETTINGS.copy()
        return self._settings[user_id_str]

    def _save_parameter(self, user_id, name, value):
        current_settings = self._get_current_settings(user_id)
        current_settings[name] = str(value)
        try:
            self._settings_saver.dump(self._settings)
        except Exception as ex:
            print(ex)
