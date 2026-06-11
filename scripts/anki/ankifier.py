import logging
from pathlib import Path
from anki.storage import Collection
from anki.notes import Note
from scripts.anki.ankiConfig import AnkiConfig, DuplicateRemoveMode
from scripts.utils.printingUtils import clearConsole, grey, italic, bold
from scripts.anki.ankiModelGen import AnkiModelGen
from scripts.anki.ankiDeckGen import AnkiDeckGen
from scripts.anki.ankiNoteGen import AnkiNoteGen
from anki.errors import DBError
import asyncio
import os
import re
from collections import defaultdict
import math

class Ankifier():
    logger = logging.getLogger(__name__)
    def __init__(self, anki_config: AnkiConfig):
        self.config = anki_config
        self.duplicate_resolve_mode = anki_config.dupl_resolve
        self.model_name = "EZAnkiAdder-LSF"
        self.col_path = self.findCollections() if not anki_config.col_path else anki_config.col_path
        if not Path(self.col_path).is_file():
            raise Ankifier.ColNotFound

    def resolveConflictingVocab(self, new_notes: list[Note]) -> list[Note]:
        def group_by(indices: list[int], values: list[str]):
            groups = defaultdict(list)
            for i in indices:
                groups[values[i]].append(i)
            return groups
        self.setDuplicateResolve()
        while True:
            clearConsole()
            print(italic(grey("Resovling duplicates")))
            def order_notes(n: Note):
                if not n.id:
                    return math.inf
                return n.id
            all_notes = sorted([self.col.get_note(n) for n in self.col.find_notes(f'note:{self.model_name}')] + new_notes, key=order_notes)
            if not all_notes:
                return
            all_ids = [n.id for n in all_notes]
            all_names = [re.sub(r'<[^>]*>', '', n["Name"]) for n in all_notes]
            # all_meanings = [n["Definitions"] for n in all_notes]
            # all_word_signs = [n["Word Signs"] for n in all_notes]
            # all_sign_writings = [n["Sign Writings"] for n in all_notes]

            name_groups = group_by(range(len(all_notes)), all_names)
            deleted_notes = False
            for name_inds in name_groups.values():
                if len(name_inds) <= 1:
                    continue
                if len(name_inds) > 1:
                    if self.duplicate_resolve_mode == DuplicateRemoveMode.UPDATE:
                        self.transferNoteData(all_notes, all_ids, new_notes, name_inds)
                    elif self.duplicate_resolve_mode == DuplicateRemoveMode.OLDEST:
                        self.keepOldest(all_notes, all_ids, new_notes, name_inds)
                    elif self.duplicate_resolve_mode == DuplicateRemoveMode.NEWEST:
                        self.keepOldest(all_notes, all_ids, new_notes, name_inds)
                    deleted_notes = True
                    break

            
            if not deleted_notes:
                break
        return new_notes


    def transferNoteData(self, all_notes: list[Note], all_ids: list[int], new_notes: list[Note],  indices: list[int]):
        oldest_note = all_notes[indices[0]]
        newest_note = all_notes[indices[-1]]
        for field_name in newest_note.keys():
            if field_name in oldest_note:
                oldest_note[field_name] = newest_note[field_name]
        if not oldest_note in new_notes:
            self.col.update_note(oldest_note)
        self.keepOldest(all_notes, all_ids, new_notes, indices)

    def keepOldest(self, all_notes: list[Note], all_ids: list[int], new_notes: list[Note],  indices: list[int]):
        for r in indices[1:]:
            if all_ids[r] == 0:
                new_notes.remove(all_notes[r])
        self.col.remove_notes([all_ids[i] for i in indices[1:]])

    def keepYoungest(self, all_notes: list[Note], all_ids: list[int], new_notes: list[Note],  indices: list[int]):
        for r in indices[:-1]:
            if all_ids[r] == 0:
                new_notes.remove(all_notes[r])
        self.col.remove_notes([all_ids[i] for i in indices[:-1]])

    def setDuplicateResolve(self):
        while self.duplicate_resolve_mode == DuplicateRemoveMode.NONE:
            clearConsole()
            print(grey("Select duplicate resolution mode"))
            print(bold("\t1. ") + f"Keep oldest {grey('(keeps learning data)')}")
            print(bold("\t2. ") + f"Keep newest {grey('(updates card but deletes learning data)')}")
            print(bold("\t3. ") + f"Transfer newest data to oldest {grey('(best of both worlds)')}")
            print(bold("\t4. ") + f"Select for each")
            response = re.match(r'^[1-4]$', input(grey(": ")))
            if response:
                self.duplicate_resolve_mode = DuplicateRemoveMode(int(response.group()) - 1)


    async def __aenter__(self):
        clearConsole()
        try:
            self.col = Collection(self.col_path)
        except DBError as e:
            raise Ankifier.AnkiAlreadyOpen
        print(italic(grey("Warming up Anki...")))
        model_gen = AnkiModelGen(self.col, self.model_name)
        self.model = model_gen.findModel()
        deck_gen = AnkiDeckGen(self.col)
        self.decks = deck_gen.findDecks()
        self.note_gen = AnkiNoteGen(self.col, self.decks, self.model)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.col.close()

    async def checkAnkiIntegrity(self):
        clearConsole()
        print(italic(grey("Checking Anki integrity...")))
        await asyncio.to_thread(self.col.fix_integrity)
        print("Integrity check complete")

    def findCollections(self, config_files: list[str] = ['./searchConfig.txt']) -> Path:
        clearConsole()
        supposed_collection_folder = Path(*Path('.').absolute().parts[0:3] + ("AppData/Roaming/Anki2",))
        if not os.path.isdir(supposed_collection_folder):
            raise Ankifier.ColNotFound
        data_bases = {}
        for dir in os.listdir(supposed_collection_folder):
            coll_path = Path(supposed_collection_folder).joinpath(dir).joinpath("collection.anki2")
            if coll_path.is_file():
                data_bases[dir] = coll_path

        if len(data_bases.keys()) == 1:
            output = list(data_bases.values())[0]
            self.writeColPathInConfigFile(output, config_files)
            return output
        
        print(grey("Please select a Anki collection :"))
        for i, k in enumerate(data_bases.keys()):
            print("\t" + bold(f'{i}. {k}'))
        
        while True:
            response = re.match(r'\d+', input(grey(": ")))
            if response and int(response.group(0)) < len(data_bases.keys()):
                output = list(data_bases.values())[int(response.group(0))]
                self.writeColPathInConfigFile(output, config_files)
                # for file in config_files:
                return output
        
    @staticmethod
    def writeColPathInConfigFile(colpath: Path, config_file: Path):
        for conf_file in config_file:
            with open(conf_file, 'r') as f:
                lines = f.read()
            lines = re.sub(r'(?m:(?<=^anki_collection_file_path=).*$)', colpath.as_posix(), lines)
            with open(conf_file, 'w') as f:
                f.write(lines)  

    class ColNotFound(Exception):
        def __init__(self, *args):
            super().__init__(*args)
    class AnkiAlreadyOpen(Exception):
        def __init__(self, *args):
            super().__init__(*args)
    