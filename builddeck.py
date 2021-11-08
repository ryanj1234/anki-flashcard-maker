import os
import logging
import genanki


def to_html(defs, part_of_speech):
    html_str = "<b>{}</b>".format(part_of_speech)
    html_str += "<ol>"
    for d in defs:
        html_str += "<li>{}</li>".format(d.text)
        if d.examples:
            html_str += "<div class=examples><ul>"
            for example in d.examples:
                html_str += f"<li>{example.text} - {example.translation}</li>"
            html_str += "</ul></div>"

    html_str += "</ol>"
    return html_str


def get_deck(language):
    if language.upper() == 'RUSSIAN':
        return RussianVocabDeck()
    elif language.upper() == 'SPANISH':
        return SpanishVocabDeck()
    elif language.upper() == 'ITALIAN':
        return ItalianVocabDeck()
    elif language.upper() == 'GERMAN':
        return GermanVocabDeck()
    else:
        raise Exception(f"Unimplemented language {language}")


class VocabDeck:
    def __init__(self, guid, name, model):
        self.logger = logging.getLogger(__name__)
        self.guid = guid
        self.name = name
        self.deck = genanki.Deck(
            guid,
            name)
        self.model = genanki.Model(
            model['guid'],
            model['name'],
            fields=model['fields'],
            css=model['css'],
            templates=model['templates']
        )
        self.media_files = []

    def add_note(self, front, back, audio_file=''):
        if audio_file:
            fname = os.path.split(audio_file)[-1]
            audio = '[sound:' + fname + ']'
            self.media_files.append(audio_file)
        else:
            audio = ''

        note = genanki.Note(model=self.model, fields=[front, back, audio])
        self.deck.add_note(note)

    def add_flashcard(self, card):
        self.logger.debug("Adding word: {}".format(card.word))
        self.logger.debug("Adding defs: {}".format(to_html(card.definitions, card.part_of_speech)))
        self.logger.debug("Adding audio: {}".format(card.audio_file))
        audio_file = '' if card.audio_file is None else card.audio_file
        self.add_note(card.word, to_html(card.definitions, card.part_of_speech), audio_file)

    def write_to_collection(self):
        self.deck.write_to_collection_from_addon()

    def export(self, out_file='output.apkg'):
        package = genanki.Package(self.deck)
        package.media_files = self.media_files
        package.write_to_file(out_file)


class RussianVocabDeck(VocabDeck):
    def __init__(self):
        guid = 205940011
        name = 'Auto Generated Vocab'
        model = {
            'guid': 1607392313,
            'name': 'Auto Vocab With Examples',
            'fields': [
                {'name': 'Front'},
                {'name': 'Back'},
                {'name': 'Audio'},
            ],
            'css': '.card {font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white;} .front .examples { display:none }',
            'templates': [
                {
                    'name': 'Card 1',
                    'qfmt': 'Listen...<br>{{Audio}}',
                    'afmt': '{{FrontSide}}<hr id="answer">{{Back}}',
                },
                {
                    'name': 'Card 2',
                    'qfmt': '<div class=front>{{Back}}</div>',
                    'afmt': '{{Back}}<hr id="answer">{{Front}}{{Audio}}',
            }]
        }

        super().__init__(guid, name, model)


class SpanishVocabDeck(VocabDeck):
    def __init__(self):
        guid = 674801255
        name = 'Spanish Auto Generated Vocab'
        model = {
            'guid': 146379426,
            'name': 'Auto Vocab With Examples Show Word',
            'fields': [
                {'name': 'Front'},
                {'name': 'Back'},
                {'name': 'Audio'},
            ],
            'css': '.card {font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white;} .front .examples { display:none }',
            'templates': [
                {
                    'name': 'Card 1',
                    'qfmt': '{{Front}}<br>{{Audio}}',
                    'afmt': '{{Front}}<hr id="answer">{{Back}}',
                },
                {
                    'name': 'Card 2',
                    'qfmt': '<div class=front>{{Back}}</div>',
                    'afmt': '{{Back}}<hr id="answer">{{Front}}{{Audio}}',
            }]
        }

        super().__init__(guid, name, model)


class ItalianVocabDeck(VocabDeck):
    def __init__(self):
        guid = 474811349
        name = 'Italian Auto Generated Vocab'
        model = {
            'guid': 146379426,
            'name': 'Auto Vocab With Examples Show Word',
            'fields': [
                {'name': 'Front'},
                {'name': 'Back'},
                {'name': 'Audio'},
            ],
            'css': '.card {font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white;} .front .examples { display:none }',
            'templates': [
                {
                    'name': 'Card 1',
                    'qfmt': '{{Front}}<br>{{Audio}}',
                    'afmt': '{{Front}}<hr id="answer">{{Back}}',
                },
                {
                    'name': 'Card 2',
                    'qfmt': '<div class=front>{{Back}}</div>',
                    'afmt': '{{Back}}<hr id="answer">{{Front}}{{Audio}}',
            }]
        }

        super().__init__(guid, name, model)


class GermanVocabDeck(VocabDeck):
    def __init__(self):
        guid = 268124051
        name = 'German Auto Generated Vocab'
        model = {
            'guid': 146379426,
            'name': 'Auto Vocab With Examples Show Word',
            'fields': [
                {'name': 'Front'},
                {'name': 'Back'},
                {'name': 'Audio'},
            ],
            'css': '.card {font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white;} .front .examples { display:none }',
            'templates': [
                {
                    'name': 'Card 1',
                    'qfmt': '{{Front}}<br>{{Audio}}',
                    'afmt': '{{Front}}<hr id="answer">{{Back}}',
                },
                {
                    'name': 'Card 2',
                    'qfmt': '<div class=front>{{Back}}</div>',
                    'afmt': '{{Back}}<hr id="answer">{{Front}}{{Audio}}',
            }]
        }

        super().__init__(guid, name, model)