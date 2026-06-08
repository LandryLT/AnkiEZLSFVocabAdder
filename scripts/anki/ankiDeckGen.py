from anki.storage import Collection
from anki.decks import DeckDict
import logging
from typing import NamedTuple
from scripts.anki.ankiNoteGen import word_type_regex

class EZDecks(NamedTuple):
    Base: DeckDict
    Nom: DeckDict
    Verbe: DeckDict
    Adjectif: DeckDict
    Adverbe: DeckDict
    Determinant: DeckDict
    Preposition: DeckDict
    Pronom: DeckDict
    Conjonction: DeckDict
    Interjection: DeckDict

class AnkiDeckGen():
    logger = logging.getLogger(__name__)
    def __init__(self, col:  Collection):
        self.col = col
    
    def findDecks(self) -> EZDecks:
        deck_tree = self._deckTreeBuilder()
        all_deck_names = self._getDeckTreePaths(deck_tree)
        all_decks = self.col.decks.all_names_and_ids()
        for deck_name in all_deck_names.values():
            if deck_name not in [d.name for d in all_decks]:
                self.logger.info(f'{deck_name} not found, creating new deck')
                new_deck = self.col.decks.new_deck()
                new_deck.name = deck_name
                self.col.decks.add_deck(new_deck)
        
        return EZDecks(**{key: self.col.decks.by_name(deck_name) for key, deck_name in all_deck_names.items()})
    
    @staticmethod
    def _getDeckTreePaths(deck_tree: dict, join_with: str = "::") -> dict[str, str]:
        output = {"Base": "EZ-LSF"}
        def recursive_branch_finder(tree: dict, c_branch: list):
            for k, v in tree.items():
                new_branch = c_branch.copy()
                new_branch.append(k)
                if isinstance(v, dict):
                    if not v.keys():
                        output[k] = join_with.join(new_branch)
                    else:
                        recursive_branch_finder(v ,new_branch)
        recursive_branch_finder(deck_tree, [])
        return output

    @staticmethod
    def _deckTreeBuilder():
        deck_tree = {"EZ-LSF": {}}
        for k in word_type_regex.keys():
            deck_tree["EZ-LSF"][k] = {}
        return deck_tree