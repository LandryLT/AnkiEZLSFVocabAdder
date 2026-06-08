from anki.storage import Collection
from anki.decks import DeckDict
from anki.notes import Note
from anki.models import NotetypeDict
from scripts.scrappers.ScrapperResults import ScrapperResult
from pathlib import Path
import re

word_type_regex = {
    "Nom": re.compile("n\.((m|f)\.)?"),
    "Verbe": re.compile("v\."),
    "Adjectif": re.compile("adj\."),
    "Adverbe": re.compile("adv\."),
    "Determinant": re.compile("det\."),
    "Preposition": re.compile("prp\."),
    "Pronom": re.compile("pro\."),
    "Conjonction": re.compile("cnj\."),
    "Interjection": re.compile("int\."),
}


class AnkiNoteGen():
    def __init__(self, col: Collection, decks, model: NotetypeDict):
        self.col = col
        self.decks = decks
        self.model = model

    def addVideo(self, filepath:str):
        self.col.media.add_file(filepath)

    def genNewNote(self, rez: ScrapperResult):
        new_note = self.col.new_note(self.model)
        new_note["Name"] = f'<div id="name">{rez.gloss}</div>'
        new_note["Typology"] = f'<div id="typology">({rez.typology})</div>'
        new_note["Definitions"] = "".join([f'<div class="definition">{meaning.definition}</div>' for meaning in rez.meanings])
        new_note["Word Signs"] = "".join(["".join([f'<div class="video"><video controls><source src="{self.addVideo(wsu)}"></video></div>' for wsu in meaning.word_signs_urls]) for meaning in rez.meanings])
        new_note["Definition Signs"] = "".join(["".join([f'<div class="video"><video controls><source src="{self.addVideo(dsu)}"></video></div>' for dsu in meaning.def_signs_urls]) for meaning in rez.meanings])
        new_note["Sign Writings"] = "".join([f'<div class="signwriting">{sw}</div>' for sw in rez.sign_writings])
        return new_note

    def submitNoteToDeck(self, note: Note):
        for deck_name, deck in self.decks._asdict().items():
            if deck_name == "Base":
                continue
            if re.search(word_type_regex[deck_name], note["Typology"]):
                self.col.add_note(note, deck["id"])
                return
        self.col.add_note(note, self.decks.Base["id"])
