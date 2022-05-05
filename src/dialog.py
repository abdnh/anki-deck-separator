from concurrent.futures import Future
from typing import Dict, List, Optional

import anki
from anki.cards import CardId
from anki.collection import SearchNode
from anki.decks import DeckId
from anki.notes import NoteId
from aqt import qtmajor
from aqt.deckchooser import DeckChooser
from aqt.main import AnkiQt
from aqt.qt import *
from aqt.utils import askUserDialog, showWarning

from . import consts

try:
    from anki.utils import strip_html
except ImportError:
    from anki.utils import stripHTML as strip_html

if qtmajor > 5:
    from .forms.form_qt6 import Ui_Dialog
else:
    from .forms.form_qt5 import Ui_Dialog  # type: ignore


ANKI_POINT_VERSION = int(anki.version.split(".")[-1])


class MyDeckChooser(DeckChooser):

    onDeckChanged = pyqtSignal(object)

    def choose_deck(self) -> None:
        super().choose_deck()
        self.onDeckChanged.emit(self.selectedId())


class DeckSeparatorDialog(QDialog):
    DECK_LIMIT = 25

    def __init__(self, mw: AnkiQt, parent: QWidget):
        super().__init__(parent)
        self.mw = mw
        self.config = mw.addonManager.getConfig(__name__)
        self.setup_ui()

    def update_fields(self, did: DeckId) -> None:
        self.nids: List[NoteId] = []
        self.fields: List[str] = []
        search = self.mw.col.build_search_string(
            SearchNode(deck=self.mw.col.decks.get(did)["name"])
        )
        self.mw.progress.start(parent=self, label="Getting field names...")
        self.mw.progress.set_title(consts.ADDON_NAME)

        def collect_fields() -> None:
            for nid in self.mw.col.find_notes(search):
                self.nids.append(nid)
                note = self.mw.col.get_note(nid)
                for field in note.keys():
                    if field not in self.fields:
                        self.fields.append(field)

        def on_done(fut: Future) -> None:
            try:
                fut.result()
            finally:
                self.form.separatorFieldComboBox.clear()
                self.form.separatorFieldComboBox.addItems(self.fields)
                parent_deck = self.mw.col.decks.immediate_parent(
                    self.mw.col.decks.name(did)
                )
                if not parent_deck:
                    parent_deck = ""
                self.form.parentDeckLineEdit.setText(parent_deck)
                self.mw.progress.finish()

        self.mw.taskman.run_in_background(collect_fields, on_done=on_done)

    def setup_ui(self) -> None:
        self.form = Ui_Dialog()
        self.form.setupUi(self)
        self.setWindowTitle(consts.ADDON_LONG_NAME)
        qconnect(self.form.processButton.clicked, self.on_process)
        if ANKI_POINT_VERSION >= 50:
            self.deck_chooser = MyDeckChooser(
                self.mw,
                self.form.deckChooser,
                label=False,
                on_deck_changed=self.update_fields,
            )
        else:
            self.deck_chooser = MyDeckChooser(
                self.mw, self.form.deckChooser, label=False
            )
            qconnect(self.deck_chooser.onDeckChanged, self.update_fields)

    def exec(self) -> int:
        self.update_fields(self.mw.col.decks.current()["id"])
        separator_field = self.config["separator_field"]
        if separator_field := self._get_field(self.fields, separator_field):
            self.form.separatorFieldComboBox.setCurrentText(separator_field)
        return super().exec()

    def accept(self) -> None:
        self.deck_chooser.cleanup()
        return super().accept()

    def _get_field(self, fields: List[str], key: str) -> Optional[str]:
        for field in fields:
            if key.lower() == field.lower():
                return field
        return None

    def _collect_decks(self, separator_field: str) -> Dict[str, List[CardId]]:
        decks: Dict[str, List[CardId]] = {}
        for i, nid in enumerate(self.nids):
            note = self.mw.col.get_note(nid)
            if separator_field not in note:
                continue
            field_value = strip_html(note[separator_field])
            if field_value:
                decks.setdefault(field_value, [])
                decks[field_value].extend(note.card_ids())
            if i % 100 == 0:
                self.mw.taskman.run_on_main(
                    lambda i=i: self.mw.progress.update(
                        f"Processed {i+1} out of {len(self.nids)} notes..."
                    )
                )
        return decks

    def _process(self, parent_deck: str, decks: Dict[str, List[CardId]]) -> int:
        for stem, cids in decks.items():
            deck_name = stem
            if parent_deck:
                deck_name = f"{parent_deck}::{deck_name}"
            deck_id = self.mw.col.decks.id(deck_name)
            self.mw.taskman.run_on_main(
                lambda cids=cids, deck_name=deck_name: self.mw.progress.update(
                    f"Moving {len(cids)} cards to deck {deck_name}..."
                )
            )
            self.mw.col.set_deck(cids, deck_id)
        return len(decks)

    def on_process(self) -> None:
        if self.form.separatorFieldComboBox.currentIndex() < 0:
            showWarning(
                "No cards in the selected deck. Please choose another deck.",
                parent=self,
                title=consts.ADDON_NAME,
            )
            return
        separator_field = self.fields[self.form.separatorFieldComboBox.currentIndex()]
        parent_deck = self.form.parentDeckLineEdit.text()
        self.config["separator_field"] = separator_field
        self.mw.addonManager.writeConfig(__name__, self.config)

        def on_done(fut: Future) -> None:
            try:
                self.deck_count = fut.result()
            finally:
                self.mw.progress.finish()
            self.accept()

        def on_done_collecting_decks(fut: Future) -> None:
            try:
                decks = fut.result()
            except Exception as exc:
                raise exc
            finally:
                self.mw.progress.finish()
            if len(decks) > self.DECK_LIMIT:
                dialog = askUserDialog(
                    f"""
This will result in creating more than {self.DECK_LIMIT} decks. \
Note that large deck list trees can break display and result in a blank screen \
in Anki versions before 2.1.50. Are you sure you want to continue?
                """,
                    ["Continue", "Abort"],
                    self,
                    title=consts.ADDON_NAME,
                )
                dialog.setDefault(1)
                ret = dialog.run()
                if ret == "Abort":
                    return
            if not decks:
                showWarning(
                    "Chosen field is empty in all notes",
                    parent=self,
                    title=consts.ADDON_NAME,
                )
                return
            self.mw.progress.start(label="Creating decks...")
            self.mw.progress.set_title(consts.ADDON_NAME)
            self.mw.taskman.run_in_background(
                lambda: self._process(parent_deck, decks),
                on_done=on_done,
            )

        self.mw.progress.start(parent=self)
        self.mw.progress.set_title(consts.ADDON_NAME)
        self.mw.taskman.run_in_background(
            lambda: self._collect_decks(separator_field),
            on_done=on_done_collecting_decks,
        )
