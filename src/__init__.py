from aqt import mw
from aqt.qt import *
from aqt.utils import tooltip

from . import consts
from .dialog import DeckSeparatorDialog


def on_action_triggered() -> None:
    dialog = DeckSeparatorDialog(mw, mw)
    if dialog.exec():
        tooltip(f"Procesed {dialog.deck_count} decks", parent=mw)
        mw.reset()


config = mw.addonManager.getConfig(__name__)
a = QAction(consts.ADDON_NAME, mw)
a.setShortcut(config["shortcut"])
qconnect(a.triggered, on_action_triggered)
mw.form.menuTools.addSeparator()
mw.form.menuTools.addAction(a)
