import os
import sys
import time
from aqt import mw
from aqt.utils import showInfo, qconnect, showCritical
from aqt.qt import *

# import modules from local path
# (insert needed in order to skip system packages)
folder = os.path.dirname(__file__)
libfolder = os.path.join(folder, "vendor")
sys.path.insert(0, libfolder)

from PyQt5 import QtCore
from PyQt5.QtCore import QThread, pyqtSignal
import PyQt5.QtWidgets

from . builddeck import get_deck
from . flashcard import Flashcard
from . pyforvo import ForvoParser
from . russianwiktionaryparser import WiktionaryParser
from . manual_parser import ManualParser
from . builddeck import to_html


LANGUAGE_CODES = {
    'Russian': 'ru',
    'Spanish': 'es'
}


class ProcessWords(QThread):
    word_start = pyqtSignal(str)
    label_update = pyqtSignal(str)
    word_done = pyqtSignal(int)
    word_not_found = pyqtSignal(str)
    add_card = pyqtSignal(Flashcard)
    need_decision = pyqtSignal(Flashcard)
    done = pyqtSignal()

    WORD_FOUND = 1
    WORD_NOT_FOUND = 2
    WORD_FOUND_NO_AUDIO = 2

    def __init__(self, words: list, language: str, language_code: str):
        super().__init__()
        self.words = words
        self.stop = False
        self.decision = -1
        self.language = language
        self.language_code = language_code

    def run(self):
        for i, word in enumerate(self.words):
            self.label_update.emit(f'Checking word {word}')
            if ':' in word:
                card = Flashcard(word, ManualParser(language=self.language), ForvoParser(language=self.language_code))
            else:
                card = Flashcard(word, WiktionaryParser(language=self.language), ForvoParser(language=self.language_code))
            if len(card.entries) == 0:
                self.word_done.emit(ProcessWords.WORD_NOT_FOUND)
                self.word_not_found.emit(word)
            elif len(card.entries) == 1:
                self.word_done.emit(ProcessWords.WORD_FOUND)
                self.add_card.emit(card)
            else:
                # get decision
                self.need_decision.emit(card)
                while self.decision < 0:
                    time.sleep(0.1)

                card.select_entry(self.decision)
                self.decision = -1
                self.word_done.emit(ProcessWords.WORD_FOUND)
                self.add_card.emit(card)

            if self.stop:
                break
        self.done.emit()

    def get_decision(self, decision):
        self.decision = decision


class ProgressBar(PyQt5.QtWidgets.QProgressDialog):
    make_decision = pyqtSignal(int)

    def __init__(self, words, *args, **kwargs):
        super(ProgressBar, self).__init__(*args, **kwargs)
        self.words = words
        self.num_words = len(words)
        self.setMaximum(self.num_words)
        self.setWindowTitle('Processing Words')
        self.setLabelText('Beginning')
        self.progress = 0
        self.choice = None

    def on_label_update(self, label_text):
        self.setLabelText(label_text)

    def on_count_changed(self, value):
        self.progress = self.progress + 1
        self.setValue(self.progress)

    def get_decision(self, card):
        self.choice = WordChoice(card)
        self.choice.decision_made.connect(self.made_decision)
        self.choice.show()

    def made_decision(self, decision):
        self.choice.hide()
        self.make_decision.emit(decision)


def get_config():
    config = mw.addonManager.getConfig(__name__)
    if config.get('LANGUAGE') is None:
        config['LANGUAGE'] = 'Russian'
    return config


class ResultsDisplay(PyQt5.QtWidgets.QWidget):
    def __init__(self, cards: [Flashcard], not_found: list, language, *args, **kwargs):
        super(ResultsDisplay, self).__init__(*args, **kwargs)
        self.cards = cards
        self.not_found = not_found

        self.deck = get_deck(language)
        self.vbox = PyQt5.QtWidgets.QVBoxLayout()

        self.statsLabel = PyQt5.QtWidgets.QLabel(f'Cards created: {len(self.cards)}<br>Cards not found: {len(self.not_found)}')
        self.statsLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.not_found_list = PyQt5.QtWidgets.QListWidget()
        self.not_found_list.setFixedHeight(100)
        for word in self.not_found:
            self.not_found_list.addItem(PyQt5.QtWidgets.QListWidgetItem(word))

        self.vbox.addWidget(self.statsLabel)
        self.vbox.addWidget(PyQt5.QtWidgets.QLabel('Not found'))
        self.vbox.addWidget(self.not_found_list)
        self.vbox.addWidget(PyQt5.QtWidgets.QLabel('Found'))

        self.table = PyQt5.QtWidgets.QTableWidget()
        header_labels = ['Word', 'Part of Speech', 'definitions', 'Has Audio']
        self.table.setColumnCount(len(header_labels))
        self.table.setRowCount(len(self.cards))
        self.table.setHorizontalHeaderLabels(header_labels)
        for row, card in enumerate(self.cards):
            self.deck.add_flashcard(card)
            self.table.setItem(row, 0, PyQt5.QtWidgets.QTableWidgetItem(card.word))
            self.table.setItem(row, 1, PyQt5.QtWidgets.QTableWidgetItem(card.part_of_speech))
            def_str = ''
            for i, definition in enumerate(card.definitions):
                def_str += f'{i+1}. {definition.text} '
            self.table.setItem(row, 2, PyQt5.QtWidgets.QTableWidgetItem(def_str))
            self.table.setItem(row, 3, PyQt5.QtWidgets.QTableWidgetItem(str(card.audio_file != '')))

        self.vbox.addWidget(self.table)

        self.export_button = PyQt5.QtWidgets.QPushButton('Export')
        # self.cancel_button = QPushButton('Cancel')

        self.export_button.clicked.connect(self.export_deck)
        # self.cancel_button.clicked.connect(QApplication.instance().quit)

        hbox = PyQt5.QtWidgets.QHBoxLayout()
        hbox.addWidget(self.export_button)
        # hbox.addWidget(self.cancel_button)
        self.vbox.addLayout(hbox)

        self.vbox.setSpacing(10)

        self.setLayout(self.vbox)
        self.setWindowTitle('Results')
        self.resize(500, self.height())

    def export_deck(self):
        self.deck.write_to_collection()
        self.close()
        showInfo("Deck has been exported")
        # msg = QMessageBox()
        # msg.setText('Deck has been exported')
        # msg.exec()


class WordEntry(PyQt5.QtWidgets.QMainWindow):
    WIDTH = 500
    HEIGHT = 500

    switch_window = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.textEdit = None
        self.init_ui()

    def init_ui(self):
        self.textEdit = PyQt5.QtWidgets.QTextEdit()
        self.setCentralWidget(self.textEdit)

        start_act = PyQt5.QtWidgets.QAction(self.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DialogApplyButton), 'Process', self)
        start_act.setStatusTip('Begin Processing')
        start_act.triggered.connect(self.process_words)

        open_act = PyQt5.QtWidgets.QAction(self.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DialogOpenButton), 'Open', self)
        open_act.setShortcut('Ctrl+O')
        open_act.setStatusTip('Open Text File')
        open_act.triggered.connect(self.select_file)

        self.statusBar()

        toolbar = self.addToolBar('asdf')
        toolbar.addAction(start_act)
        toolbar.addAction(open_act)

        self.textEdit.setStyleSheet(
            "margin: 10px 10px 0px; padding: 1px;"
            "border-style: solid; border-radius: 3px; border-width: 0.5px; border-color: rgba(0,140,255,255);")

        self.resize(WordEntry.WIDTH, WordEntry.HEIGHT)
        self.center()
        self.setWindowTitle('Flashcard Maker')

    def center(self):
        qr = self.frameGeometry()
        cp = PyQt5.QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def select_file(self):
        options = PyQt5.QtWidgets.QFileDialog.Options()
        options |= PyQt5.QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = PyQt5.QtWidgets.QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "All Files (*);;Python Files (*.py)", options=options)
        if file_name:
            with open(file_name, 'r', encoding='utf-8') as f:
                data = f.read()
            self.textEdit.setText(data)

    def set_data(self, data):
        self.textEdit.setText(data)

    def process_words(self):
        text = self.textEdit.toPlainText()
        tmp_words = text.split('\n')
        words = [word for word in tmp_words if word]
        num_words = len(words)
        reply = PyQt5.QtWidgets.QMessageBox.question(self, 'Message',
                                     f"Process {num_words} words?", PyQt5.QtWidgets.QMessageBox.Yes |
                                                     PyQt5.QtWidgets.QMessageBox.No, PyQt5.QtWidgets.QMessageBox.Yes)
        if reply == PyQt5.QtWidgets.QMessageBox.Yes:
            self.switch_window.emit(words)


class Controller:
    def __init__(self, language: str, language_code: str):
        self.word_entry = None
        self.no_def = []
        self.no_audio = []
        self.cards = []

        self.progress_bar = None
        self.process_thread = None
        self.results = None

        self.language = language
        self.language_code = language_code

    def show_word_entry(self, words):
        self.word_entry = WordEntry()
        self.word_entry.set_data(words)
        self.word_entry.switch_window.connect(self.start_processing)
        self.word_entry.show()

    def start_processing(self, words):
        mw.progress_bar = ProgressBar(words, parent=self.word_entry)
        self.progress_bar = mw.progress_bar
        self.process_thread = ProcessWords(words, self.language, self.language_code)
        self.process_thread.start()
        self.process_thread.label_update.connect(self.progress_bar.on_label_update)
        self.process_thread.word_done.connect(self.progress_bar.on_count_changed)
        self.process_thread.word_not_found.connect(self.word_not_found)
        self.process_thread.add_card.connect(self.on_add_card)
        self.process_thread.need_decision.connect(self.progress_bar.get_decision)
        self.progress_bar.make_decision.connect(self.process_thread.get_decision)
        self.process_thread.done.connect(self.display_results)
        self.progress_bar.show()

    def on_add_card(self, card):
        self.cards.append(card)

    def display_results(self):
        self.results = ResultsDisplay(self.cards, self.no_def, self.language)
        self.results.show()
        self.word_entry.close()

    def word_not_found(self, word):
        self.no_def.append(word)


def run_addon() -> None:
    config = get_config()

    if config.get('FORVO_API_KEY'):
        os.environ['FORVO_API_KEY'] = config['FORVO_API_KEY']

    language = config['LANGUAGE']
    if language not in LANGUAGE_CODES:
        showCritical(f"Language {language} not supported")
    else:
        if 'FILE_NAME' in config:
            # file = get_full_file_path(config['FILE_NAME'])
            words = get_words(config['FILE_NAME'])
        else:
            words = ""
        mw.controller = controller = Controller(language, LANGUAGE_CODES[language])
        controller.show_word_entry(words)


def get_full_file_path(file_name: str) -> str:
    file = os.path.join(os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop'), file_name)
    return file


def set_menu_item() -> None:
    action = PyQt5.QtWidgets.QAction("Run Card Generator", mw)
    qconnect(action.triggered, run_addon)
    mw.form.menuTools.addAction(action)


def get_words(input_file: str) -> str:
    words = ""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            words = f.read()
    except IOError:
        showCritical(f"Could not open file {input_file}")
    return words


class EntryChoice(PyQt5.QtWidgets.QPushButton):
    def __init__(self, num, text):
        super(EntryChoice, self).__init__(text)
        self.num = num


class WordChoice(PyQt5.QtWidgets.QWidget):
    decision_made = pyqtSignal(int)

    def __init__(self, card):
        super(WordChoice, self).__init__()

        self.setWindowTitle('Choose Entry')

        grid = PyQt5.QtWidgets.QGridLayout()
        grid.setSpacing(10)

        for i, card in enumerate(card.entries):
            button1 = EntryChoice(i, f'{card.word}')
            button1.clicked.connect(self.on_choose)
            card1 = PyQt5.QtWidgets.QLabel(to_html(card.definitions, card.part_of_speech))

            grid.addWidget(button1, i, 0)
            grid.addWidget(card1, i, 1)

        self.setLayout(grid)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = PyQt5.QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def on_choose(self):
        self.decision_made.emit(self.sender().num)


set_menu_item()
