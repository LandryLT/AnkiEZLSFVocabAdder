from scripts.scrappers.Scrapper import Scrapper
import asyncio
from unidecode import unidecode
from asyncio import gather
from scripts.caching.cacheSearch import SearchCache
from scripts.scrappers.ScrapperResults import SPResult, SPPreResult
import re

signpuddle_cache = SearchCache("./cache/signpuddle")

class SignPuddleScrapper(Scrapper):
    def __init__(self, session, wait_between_requests:float = 0):
        self.wait_between_requests = wait_between_requests
        super().__init__(session)

    async def getSVG(self, search_term: str) -> list[str]:
        self.logger.info(f"Searching sign writing for {search_term}")
        signs = await self.__searchForSigns(search_term)
        word_signs_co = [self.__searchForSvg(sg.sign) for sg in signs if re.compile(f"^({search_term}|{unidecode(search_term)})(-[^Gg]+)?(-[0-9]+)?$", re.I).match(sg.gloss)]
        return SPResult(search_term, await gather(*word_signs_co, return_exceptions=True))

    async def __searchForSvg(self, sign: str) -> str:
        self.logger.debug(f"Getting SVG for {sign}")
        await asyncio.sleep(self.wait_between_requests)
        async with self.session.get(f"https://signpuddle.net/svg/{sign}-CZ3") as resp:
            resp.raise_for_status()
            return await resp.text()
        
    async def __searchForSigns(self, search_term: str) -> list[SPPreResult]:
        self.logger.debug(f"Getting sign for {search_term}")
        search_term = f"({search_term}|{unidecode(search_term)})" 
        data = await self._getJSONData("results", "https://signpuddle.net/puddle/sgn58/search/", search_term, "")
        return [SPPreResult(d["terms"][0], d["sign"]) for d in data]
    
    @staticmethod
    def clearCache():
        signpuddle_cache.clearCache()