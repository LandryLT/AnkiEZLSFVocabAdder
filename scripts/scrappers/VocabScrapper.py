from aiohttp import ClientSession
from scripts.scrappers.ElixScrapper import ElixScrapper
from scripts.scrappers.ScrapperResults import ScrapperResult
from scripts.scrappers.SignPuddleScrapper import SignPuddleScrapper
from tqdm.asyncio import tqdm
from scripts.utils.printingUtils import tqdm_format

class VocabScrapper():
    def __init__(self):
        pass

    async def searchTerms(self, vocab_list: list[str]):
        elix_co = [self.elix_scrap.searchWord(wrd) for wrd in vocab_list]
        print("Searching elix-lsf.fr...")
        elix_results = await tqdm.gather(*elix_co, bar_format=tqdm_format)
        
        signpuddle_co = [self.signpuddle_scrap.getSVG(er.gloss) for er in elix_results]
        print("Searching signpuddle.net...")
        signpuddle_results = await tqdm.gather(*signpuddle_co, bar_format=tqdm_format)
        output = []
        for elix, spud in zip(elix_results, signpuddle_results):
            new_sr = ScrapperResult(**elix._asdict())
            new_sr.sign_writings = spud
            output.append(new_sr)
        return output

    async def __aenter__(self):
        self.session = ClientSession()
        self.elix_scrap = ElixScrapper(self.session)
        self.signpuddle_scrap = SignPuddleScrapper(self.session)
        return self


    async def __aexit__(self, exc_type, exc, tb):
        self.session.close