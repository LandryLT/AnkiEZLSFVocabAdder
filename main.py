import asyncio
from scripts.scrappers.VocabScrapper import VocabScrapper
from scripts.utils.getVocab2Add import getVocab2Add
async def main():
    asyncio.get_event_loop().set_debug(False)
    vocab_list = getVocab2Add()
    async with VocabScrapper() as vs:
        rez = await vs.searchTerms(vocab_list)
        pass

if __name__ == '__main__':
    asyncio.run(main())