import sys
import time

from PyQt5 import QtCore
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget, QApplication, QLineEdit, QAction, QStyle, QHBoxLayout, QPushButton, QMessageBox, \
    QFileDialog, QDesktopWidget, QTextEdit, QMainWindow, QProgressBar, QProgressDialog, QDialog, QGridLayout, QLabel, \
    QInputDialog, QVBoxLayout, QListWidgetItem, QListWidget, QTableWidgetItem, QTableWidget

import builddeck
from flashcard import Flashcard
from pyforvo import ForvoParser
from russianwiktionaryparser import WiktionaryParser
from manual_parser import ManualParser
from builddeck import to_html

# language = 'Spanish'
# language_code = 'es'
language = 'Russian'
language_code = 'ru'


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

    def __init__(self, words):
        super().__init__()
        self.words = words
        self.stop = False
        self.decision = -1

    def run(self):
        for i, word in enumerate(self.words):
            self.label_update.emit(f'Checking word {word}')
            if ':' in word:
                card = Flashcard(word, ManualParser(language=language), ForvoParser(language=language_code))
            else:
                card = Flashcard(word, WiktionaryParser(language=language), ForvoParser(language=language_code))
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


class WordEntry(QMainWindow):
    WIDTH = 500
    HEIGHT = 500

    switch_window = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.textEdit = QTextEdit()
        self.setCentralWidget(self.textEdit)

        startAct = QAction(self.style().standardIcon(QStyle.SP_DialogApplyButton), 'Process', self)
        startAct.setStatusTip('Begin Processing')
        startAct.triggered.connect(self.process_words)

        openAct = QAction(self.style().standardIcon(QStyle.SP_DialogOpenButton), 'Open', self)
        openAct.setShortcut('Ctrl+O')
        openAct.setStatusTip('Open Text File')
        openAct.triggered.connect(self.select_file)

        self.statusBar()

        toolbar = self.addToolBar('asdf')
        toolbar.addAction(startAct)
        toolbar.addAction(openAct)

        self.textEdit.setStyleSheet(
            "margin: 10px 10px 0px; padding: 1px;"
            "border-style: solid; border-radius: 3px; border-width: 0.5px; border-color: rgba(0,140,255,255);")

        self.resize(WordEntry.WIDTH, WordEntry.HEIGHT)
        self.center()
        self.setWindowTitle('Flashcard Maker')

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def select_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "All Files (*);;Python Files (*.py)", options=options)
        if fileName:
            with open(fileName, 'r', encoding='utf-8') as f:
                data = f.read()
            self.textEdit.setText(data)

    def process_words(self):
        text = self.textEdit.toPlainText()
        tmp_words = text.split('\n')
        words = [word for word in tmp_words if word]
        num_words = len(words)
        reply = QMessageBox.question(self, 'Message',
                                     f"Process {num_words} words?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.switch_window.emit(words)


class ProgressBar(QProgressDialog):
    make_decision = pyqtSignal(int)

    def __init__(self, words, *args, **kwargs):
        super(ProgressBar, self).__init__(*args, **kwargs)
        self.words = words
        self.num_words = len(words)
        self.setMaximum(self.num_words)
        self.setWindowTitle('Processing Words')
        self.setLabelText('Beginning')
        self.progress = 0

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


class Controller:
    def __init__(self):
        self.word_entry = None
        self.no_def = []
        self.no_audio = []
        self.cards = []

    def show_word_entry(self):
        self.word_entry = WordEntry()
        self.word_entry.switch_window.connect(self.start_processing)
        self.word_entry.show()

    def start_processing(self, words):
        self.progress_bar = ProgressBar(words, parent=self.word_entry)
        self.process_thread = ProcessWords(words)
        self.process_thread.start()
        self.process_thread.label_update.connect(self.progress_bar.on_label_update)
        self.process_thread.word_done.connect(self.progress_bar.on_count_changed)
        self.process_thread.word_not_found.connect(self.word_not_found)
        self.process_thread.add_card.connect(self.on_add_card)
        self.process_thread.need_decision.connect(self.progress_bar.get_decision)
        self.progress_bar.make_decision.connect(self.process_thread.get_decision)
        self.process_thread.done.connect(self.display_results)
        self.progress_bar.show()
        self.word_entry.hide()

    def on_add_card(self, card):
        self.cards.append(card)

    def display_results(self):
        self.results = ResultsDisplay(self.cards, self.no_def)
        self.results.show()
        self.word_entry.close()

    def word_not_found(self, word):
        self.no_def.append(word)


class EntryChoice(QPushButton):
    def __init__(self, num, text):
        super(EntryChoice, self).__init__(text)
        self.num = num


class WordChoice(QWidget):
    decision_made = pyqtSignal(int)

    def __init__(self, card):
        super(WordChoice, self).__init__()

        self.setWindowTitle('Choose Entry')

        grid = QGridLayout()
        grid.setSpacing(10)

        for i, card in enumerate(card.entries):
            button1 = EntryChoice(i, f'{card.word}')
            button1.clicked.connect(self.on_choose)
            card1 = QLabel(to_html(card.definitions, card.part_of_speech))

            grid.addWidget(button1, i, 0)
            grid.addWidget(card1, i, 1)

        self.setLayout(grid)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def on_choose(self):
        self.decision_made.emit(self.sender().num)


class ResultsDisplay(QWidget):
    def __init__(self, cards: [Flashcard], not_found: list, *args, **kwargs):
        super(ResultsDisplay, self).__init__(*args, **kwargs)
        self.cards = cards
        self.not_found = not_found

        self.deck = builddeck.get_deck(language)
        self.init_ui()

    def init_ui(self):
        self.vbox = QVBoxLayout()

        self.statsLabel = QLabel(f'Cards created: {len(self.cards)}<br>Cards not found: {len(self.not_found)}')
        self.statsLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.not_found_list = QListWidget()
        self.not_found_list.setFixedHeight(100)
        for word in self.not_found:
            self.not_found_list.addItem(QListWidgetItem(word))

        self.vbox.addWidget(self.statsLabel)
        self.vbox.addWidget(QLabel('Not found'))
        self.vbox.addWidget(self.not_found_list)
        self.vbox.addWidget(QLabel('Found'))

        self.table = QTableWidget()
        header_labels = ['Word', 'Part of Speech', 'definitions', 'Has Audio']
        self.table.setColumnCount(len(header_labels))
        self.table.setRowCount(len(self.cards))
        self.table.setHorizontalHeaderLabels(header_labels)
        for row, card in enumerate(self.cards):
            self.deck.add_flashcard(card)
            self.table.setItem(row, 0, QTableWidgetItem(card.word))
            self.table.setItem(row, 1, QTableWidgetItem(card.part_of_speech))
            def_str = ''
            for i, definition in enumerate(card.definitions):
                def_str += f'{i+1}. {definition.text} '
            self.table.setItem(row, 2, QTableWidgetItem(def_str))
            self.table.setItem(row, 3, QTableWidgetItem(str(card.audio_file != '')))

        self.vbox.addWidget(self.table)

        self.export_button = QPushButton('Export')
        self.cancel_button = QPushButton('Cancel')

        self.export_button.clicked.connect(self.export_deck)
        self.cancel_button.clicked.connect(QApplication.instance().quit)

        hbox = QHBoxLayout()
        hbox.addWidget(self.export_button)
        hbox.addWidget(self.cancel_button)
        self.vbox.addLayout(hbox)

        self.vbox.setSpacing(10)

        self.setLayout(self.vbox)
        self.setWindowTitle('Results')
        self.resize(500, self.height())

    def export_deck(self):
        self.deck.export()
        msg = QMessageBox()
        msg.setText('Deck has been exported')
        msg.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = Controller()
    controller.show_word_entry()
    sys.exit(app.exec_())
