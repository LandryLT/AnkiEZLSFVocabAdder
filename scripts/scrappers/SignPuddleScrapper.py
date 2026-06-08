from scripts.scrappers.Scrapper import Scrapper
import asyncio
from unidecode import unidecode
from asyncio import gather
from scripts.caching.cacheSearch import SearchCache
from scripts.scrappers.ScrapperResults import SPResult

signpuddle_cache = SearchCache("./cache/signpuddle")

class SignPuddleScrapper(Scrapper):
    def __init__(self, session, wait_between_requests:float = 0):
        self.wait_between_requests = wait_between_requests
        super().__init__(session)

    async def getSVG(self, search_term: str) -> list[str]:
        self.logger.info(f"Searching sign writing for {search_term}")
        signs = await self.__searchForSigns(search_term)
        word_signs_co = [self.__searchForSvg(sg) for sg in signs[:len(signs)//2]]
        return SPResult(search_term, await gather(*word_signs_co))

    async def __searchForSvg(self, sign: str) -> str:
        self.logger.debug(f"Getting SVG for {sign}")
        await asyncio.sleep(self.wait_between_requests)
        async with self.session.get(f"https://signpuddle.net/svg/{sign}-CZ3") as resp:
            resp.raise_for_status()
            return await resp.text()
        
    async def __searchForSigns(self, search_term: str) -> list[str]:
        self.logger.debug(f"Getting sign for {search_term}")
        search_term = f"({search_term}|{unidecode(search_term)})" 
        data = await self._getJSONData("results", "https://signpuddle.net/puddle/sgn58/sign?term=", search_term)
        return [d["sign"] for d in data]
    
    @staticmethod
    def clearCache():
        signpuddle_cache.clearCache()