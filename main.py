import asyncio
from scripts.scrappers.VocabScrapper import VocabScrapper
from scripts.utils.getVocab2Add import getVocab2Add, clearVocab2Add
from scripts.utils.scrapperConfig import scrapperConfigParser
import logging
from scripts.anki.ankifier import Ankifier
from scripts.anki.ankiConfig import AnkiConfig, DuplicateRemoveMode

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.CRITICAL)
async def main():
    asyncio.get_event_loop().set_debug(False)
    config = scrapperConfigParser()
    vocab_list = getVocab2Add()
    async with Ankifier(config.ankiConfig) as ankifier:
        async with VocabScrapper() as vs:
            if not config.use_cache:
                vs.elix_scrap.clearCache()
                vs.signpuddle_scrap.clearCache()
            rez, no_rez = await vs.searchTerms(vocab_list)

        new_notes = [ankifier.note_gen.genNewNote(r) for r in rez]
        new_notes = [n for n in new_notes if n]
        resolved_notes = ankifier.resolveConflictingVocab(new_notes)
        for note in resolved_notes:
            ankifier.note_gen.submitNoteToDeck(note)

    if config.delete_cache_on_complete:
        vs.elix_scrap.clearCache()
        vs.signpuddle_scrap.clearCache()
    if config.delete_vocablist_on_complete:
        clearVocab2Add()


if __name__ == '__main__':
    asyncio.run(main())