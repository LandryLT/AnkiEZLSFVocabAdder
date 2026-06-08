import asyncio
from scripts.scrappers.VocabScrapper import VocabScrapper
from scripts.utils.getVocab2Add import getVocab2Add
import logging
from scripts.anki.ankifier import Ankifier
from scripts.anki.ankiConfig import AnkiConfig, DuplicateRemoveMode

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.CRITICAL)
async def main():
    asyncio.get_event_loop().set_debug(False)
    vocab_list = getVocab2Add()
    async with Ankifier(AnkiConfig(None, DuplicateRemoveMode.UPDATE)) as ankifier:
        async with VocabScrapper() as vs:
            rez = await vs.searchTerms(vocab_list)

        new_notes = [ankifier.note_gen.genNewNote(r) for r in rez]
        resolved_notes = ankifier.resolveConflictingVocab(new_notes)
        for note in resolved_notes:
            ankifier.note_gen.submitNoteToDeck(note)

        vs.elix_scrap.clearCache()
        vs.signpuddle_scrap.clearCache()


if __name__ == '__main__':
    asyncio.run(main())