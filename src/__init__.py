from anki.decks import DeckId
from aqt import gui_hooks, mw
from aqt.qt import *
from aqt.utils import tooltip

from . import consts
from .dialog import DeckSeparatorDialog


def on_action_triggered() -> None:
    dialog = DeckSeparatorDialog(mw, mw)
    if dialog.exec():
        tooltip(f"Processed {dialog.deck_count} decks", parent=mw)
        mw.reset()


def on_deck_browser_will_show_options_menu(menu: QMenu, did: int) -> None:
    def duplicate() -> None:
        dialog = DeckSeparatorDialog(mw, mw, starting_deck_id=DeckId(did))
        if dialog.exec(force_duplicate_deck=True):
            tooltip("Duplicated deck", parent=mw)
            mw.reset()

    action = menu.addAction("Duplicate")
    qconnect(action.triggered, duplicate)


config = mw.addonManager.getConfig(__name__)
a = QAction(consts.ADDON_NAME, mw)
a.setShortcut(config["shortcut"])
qconnect(a.triggered, on_action_triggered)
mw.form.menuTools.addSeparator()
mw.form.menuTools.addAction(a)
gui_hooks.deck_browser_will_show_options_menu.append(
    on_deck_browser_will_show_options_menu
)
