import logging
import os

_LOG = logging.getLogger(__name__)


class Flashcard(object):
    media_dir = '.'

    def __init__(self, entered_word, parser, audio_parser=None):
        self.logger = logging.getLogger(f"Flashcard_{entered_word}")
        self._parser = parser
        self._audio_parser = audio_parser

        self.entered_word = entered_word
        self._audio_file = None
        self.chosen_entry = None

        entries = self._parser.fetch(entered_word)

        if not entries:
            self.logger.debug('Using search function to find entries')
            entries = self._get_entries_from_search(entries, entered_word)

        followed_entries = self._follow_entries_to_base(entries, 0)
        word_list = []
        self._base_entries = []
        for entry in followed_entries:
            if entry.word not in word_list:
                self._base_entries.append(entry)
                word_list.append(entry.word)

        if len(self._base_entries) == 1:
            self.chosen_entry = self._base_entries[0]
            self._parse_chosen_entry()

    def _parse_chosen_entry(self):
        self.word = self.chosen_entry.word
        if self.chosen_entry.audio_links:
            self.logger.info('Downloading audio from wiktionary')
            self._download_file(self.chosen_entry.audio_links[0])
        if self._audio_file is None and self._audio_parser is not None:
            self.logger.info('Checking Forvo for pronunciations')
            self._audio_file = self._audio_parser.download(self.chosen_entry.word, Flashcard.media_dir)

    @property
    def front(self):
        return f"{self.chosen_entry.word}: {self.chosen_entry.part_of_speech}"

    @property
    def back(self):
        back_str = ""
        for i, definition in enumerate(self.chosen_entry.definitions):
            back_str += f"\t{i + 1}. {definition.text}\n"
        return back_str

    @property
    def entries(self):
        return self._base_entries

    @property
    def definitions(self):
        return self.chosen_entry.definitions

    @property
    def part_of_speech(self):
        return self.chosen_entry.part_of_speech

    @property
    def audio_file(self):
        return '' if self._audio_file is None else self._audio_file

    def __str__(self):
        self_str = ""
        for i, entry in enumerate(self._base_entries):
            self_str += f"Entry {i+1} -> {entry.word}\n\t{entry.part_of_speech}\n"
            for j, definition in enumerate(entry.definitions):
                self_str += f"\t{j+1}. {definition.text}\n"
                for example in definition.examples:
                    self_str += f"\t\t* {example.text}\n"
        return self_str

    def _follow_entries_to_base(self, entries, recursion_level):
        if recursion_level > 3:
            # raise Exception('Greater than 10 levels of recursion reached trying to follow entry to base word')
            return entries
        base_entries = []
        for entry in entries:
            followed_entries = entry.follow_to_base()
            if followed_entries:
                base_entries.extend(self._follow_entries_to_base(followed_entries, recursion_level + 1))
            else:
                base_entries.append(entry)
        return base_entries

    def _get_entries_from_search(self, entries, word):
        search_results = self._parser.search(word)
        match = check_for_match(search_results, word)
        if match is not None:
            entries = self._parser.fetch(match)
            if not entries:
                entries = self._parser.fetch(match.lower())
            else:
                for entry in entries:
                    entry.tracing.append(f'Found word from search {match}')
        else:
            if len(search_results[1]) > 0:  # wiki returned some suggestions
                max_checks = 3
                for possible_entry in search_results[3][0:max_checks]:
                    possible_entries = self._parser.fetch_from_url(possible_entry)  # fetch the first suggestion
                    stripped_word = word.lower().replace('́', '')
                    for entry in possible_entries:
                        if entry.inflections is not None:
                            inflection_set = entry.inflections.to_lower_set()
                            for inflection in inflection_set:
                                if stripped_word == inflection.lower().replace('́', '').replace('ё', 'е'):
                                    print("Found word in inflections table for %s ->" % entry.word, end=' ')
                                    entries = [entry]
                                    break
                            else:
                                continue
                            break
                        else:
                            if stripped_word == entry.word.lower().replace('́', '').replace('ё', 'е'):
                                entries = [entry]
                                entries[0].tracing.append(f"Used search to find word {entry.word}")
                                break
        return entries

    def _download_file(self, link):
        if not os.path.exists(Flashcard.media_dir):
            os.mkdir(Flashcard.media_dir)
        self._audio_file = self._parser.download_audio(link, Flashcard.media_dir)

    def select_entry(self, choice_num):
        self.chosen_entry = self._base_entries[choice_num]
        self._parse_chosen_entry()


def check_for_match(search_results, entered_word):
    match = None
    suggestions = search_results[1]
    for suggestion in suggestions:
        if entered_word == suggestion.replace('ё', 'е'):
            _LOG.debug('ё match found. Replacing %s with %s', entered_word, suggestion)
            match = suggestion
            break
        elif entered_word.lower() == suggestion.lower():
            _LOG.debug('Capitalization issue. Replacing %s with %s', entered_word, suggestion)
            match = suggestion
            break
    return match


if __name__ == '__main__':
    from russianwiktionaryparser import WiktionaryParser
    from pyforvo import ForvoParser
    logging.basicConfig(level=logging.DEBUG)
    word = 'casa'
    card = Flashcard(word, WiktionaryParser(language='Spanish'), ForvoParser(language='es'))
