import logging


class ManualDefinition:
    def __init__(self, word, definition):
        self._logger = logging.getLogger('ManualDef')
        self.base_word = word
        self.base_link = None
        self.text = definition
        self.examples = []


class ManualEntry:
    def __init__(self, word, language, pos, definition):
        self._logger = logging.getLogger('Manual-%s' % word)
        self.word = word
        self.language = language
        self.part_of_speech = pos
        self.definitions = [
            ManualDefinition(word, definition)
        ]
        self.inflections = None
        self.audio_links = []
        self.base_links = []
        self.base_links_set = set()

    def follow_to_base(self):
        return [self]

    def __str__(self):
        self_str = f"{self.word}: {self.part_of_speech}\n"
        for i, definition in enumerate(self.definitions):
            self_str += f"\t{i + 1}. {definition.text}\n"
            for example in definition.examples:
                self_str += f"\t\t{example.text} - {example.translation}\n"
        return self_str.replace('́', '')  # remove accents


class ManualParser:
    def __init__(self, language):
        self._logger = logging.getLogger('ManualParser')
        self.language = language

    def fetch(self, word):
        parts = word.split(':')
        word = parts[0]
        pos = parts[1]
        meaning = parts[2]
        return [ManualEntry(word, self.language, pos, meaning)]
