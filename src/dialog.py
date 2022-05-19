import math
from concurrent.futures import Future
from itertools import zip_longest
from typing import Dict, Iterable, List, Optional

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


def groups_of_n(iterable: Iterable, n: int) -> Iterable:
    return zip_longest(*[iter(iterable)] * n)


class MyDeckChooser(DeckChooser):

    onDeckChanged = pyqtSignal(object)

    def choose_deck(self) -> None:
        super().choose_deck()
        self.onDeckChanged.emit(self.selectedId())


class DeckSeparatorDialog(QDialog):
    DECK_LIMIT = 25

    def __init__(
        self, mw: AnkiQt, parent: QWidget, starting_deck_id: Optional[DeckId] = None
    ):
        super().__init__(parent)
        self.mw = mw
        self.config = mw.addonManager.getConfig(__name__)
        self.setup_ui(starting_deck_id)

    def update_fields(self, did: DeckId) -> None:
        deck_name = self.deck_chooser.selected_deck_name()
        self.form.duplicateDeckNameLineEdit.setText(deck_name + "_dup")
        self.nids: List[NoteId] = []
        # self.cids = List[CardId] = []
        self.fields: List[str] = []
        search = self.mw.col.build_search_string(SearchNode(deck=deck_name))
        self.mw.progress.start(parent=self, label="Getting field names...")
        self.mw.progress.set_title(consts.ADDON_NAME)

        def collect_fields() -> None:
            self.deck_tree = self.mw.col.decks.children(did) + [(deck_name, did)]
            # self.cids = self.mw.col.decks.cids(did, children=True)
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

    def setup_ui(self, starting_deck_id: Optional[DeckId]) -> None:
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
                starting_deck_id=starting_deck_id,
            )
        else:
            self.deck_chooser = MyDeckChooser(
                self.mw,
                self.form.deckChooser,
                label=False,
                starting_deck_id=starting_deck_id,
            )
            qconnect(self.deck_chooser.onDeckChanged, self.update_fields)
        qconnect(
            self.form.separatorFieldRadioButton.toggled,
            lambda t: self.form.separatorFieldComboBox.setEnabled(t),
        )
        qconnect(
            self.form.numberOfCardsRadioButton.toggled,
            lambda t: self.form.numberOfCardsSpinBox.setEnabled(t),
        )
        qconnect(
            self.form.duplicateDeckRadioButton.toggled,
            lambda t: self.form.duplicateDeckNameLineEdit.setEnabled(t),
        )

    def exec(self, force_duplicate_deck: bool = False) -> int:
        self.update_fields(self.deck_chooser.selected_deck_id)
        separator_field = self.config["separator_field"]
        number_of_notes = self.config["number_of_notes"]
        duplicate_deck = self.config["duplicate_deck"] or force_duplicate_deck
        if duplicate_deck:
            self.form.separatorFieldRadioButton.toggled.emit(False)
            self.form.numberOfCardsRadioButton.toggled.emit(False)
            self.form.duplicateDeckRadioButton.setChecked(True)
        elif separator_field := self._get_field(self.fields, separator_field):
            self.form.numberOfCardsRadioButton.toggled.emit(False)
            self.form.duplicateDeckRadioButton.toggled.emit(False)
            self.form.separatorFieldComboBox.setCurrentText(separator_field)
            self.form.separatorFieldRadioButton.setChecked(True)
        else:
            self.form.separatorFieldRadioButton.toggled.emit(False)
            self.form.duplicateDeckRadioButton.toggled.emit(False)
            self.form.numberOfCardsRadioButton.setChecked(True)
            self.form.numberOfCardsSpinBox.setValue(number_of_notes)

        return super().exec()

    def accept(self) -> None:
        self.deck_chooser.cleanup()
        return super().accept()

    def _get_field(self, fields: List[str], key: str) -> Optional[str]:
        for field in fields:
            if key.lower() == field.lower():
                return field
        return None

    def _collect_decks(
        self,
        separator_field: str,
        number_of_notes: int,
        duplicate_deck_name: str,
        deck_name: str,
    ) -> Dict[str, List[CardId]]:
        decks: Dict[str, List[CardId]] = {}
        if separator_field:
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
        elif duplicate_deck_name:
            for i, nid in enumerate(self.nids):
                note = self.mw.col.get_note(nid)
                note_type = note.note_type()
                dup_note = self.mw.col.new_note(note_type["id"])
                for key, value in note.items():
                    dup_note[key] = value
                dup_note.tags = note.tags
                self.mw.col.add_note(dup_note, DeckId(1))
                dup_note = self.mw.col.get_note(dup_note.id)
                new_cids = dup_note.card_ids()
                for cid_i, cid in enumerate(note.card_ids()):
                    card = self.mw.col.get_card(cid)
                    deck_idx = -1
                    for j, child in enumerate(self.deck_tree):
                        if card.did == child[1]:
                            deck_idx = j
                            break
                    if deck_idx != -1:
                        base_name = self.mw.col.decks.basename(
                            self.deck_tree[deck_idx][0]
                        )
                        if base_name != deck_name:
                            deck_name = duplicate_deck_name + "::" + base_name
                        else:
                            # tree root
                            deck_name = duplicate_deck_name
                        decks.setdefault(deck_name, [])
                        decks[deck_name].append(new_cids[cid_i])
                if i % 100 == 0:
                    self.mw.taskman.run_on_main(
                        lambda i=i: self.mw.progress.update(
                            f"Processed {i+1} out of {len(self.nids)} notes..."
                        )
                    )

        else:
            pad = math.ceil(math.log10(len(self.nids)))
            for i, nid_group in enumerate(groups_of_n(self.nids, number_of_notes)):
                start = str(i * number_of_notes + 1).zfill(pad)
                end = str((i + 1) * number_of_notes).zfill(pad)
                if i * number_of_notes != len(self.nids):
                    group_len = len(self.nids) - i * number_of_notes
                    nid_group = nid_group[:group_len]
                deck_name = f"{start}-{end}"
                cids: List[CardId] = []
                for nid in nid_group:
                    note = self.mw.col.get_note(nid)
                    cids.extend(note.card_ids())
                decks[deck_name] = cids
                self.mw.taskman.run_on_main(
                    lambda i=i: self.mw.progress.update(
                        f"Processed {(i+1) * number_of_notes} out of {len(self.nids)} notes..."
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
        separator_field = (
            self.fields[self.form.separatorFieldComboBox.currentIndex()]
            if self.form.separatorFieldRadioButton.isChecked()
            else ""
        )
        deck_name = self.deck_chooser.selected_deck_name()
        parent_deck = self.form.parentDeckLineEdit.text()
        number_of_notes = self.form.numberOfCardsSpinBox.value()
        duplicate_deck = self.form.duplicateDeckRadioButton.isChecked()
        duplicate_deck_name = self.form.duplicateDeckNameLineEdit.text()
        self.config["separator_field"] = separator_field
        self.config["number_of_notes"] = number_of_notes
        self.config["duplicate_deck"] = duplicate_deck
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
This will result in creating {len(decks)} decks. \
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
                if separator_field:
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
            lambda: self._collect_decks(
                separator_field, number_of_notes, duplicate_deck_name, deck_name
            ),
            on_done=on_done_collecting_decks,
        )
