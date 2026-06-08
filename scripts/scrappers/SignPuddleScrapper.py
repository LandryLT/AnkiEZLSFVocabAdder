from scripts.scrappers.Scrapper import Scrapper
import re 
from unidecode import unidecode
from asyncio import gather
class SignPuddleScrapper(Scrapper):
    def __init__(self, session):
        super().__init__(session)

    async def getSVG(self, search_term: str) -> list[str]:
        signs = await self.__searchForSigns(search_term)
        word_signs_co = [self.__searchForSvg(sg) for sg in signs]
        return await gather(*word_signs_co)

    async def __searchForSvg(self, sign: str) -> str:
        async with self.session.get(f"https://signpuddle.net/svg/{sign}-CZ3") as resp:
            resp.raise_for_status()
            return await resp.text()
        
    async def __searchForSigns(self, search_term: str) -> list[str]:
        search_term = f"({search_term}|{unidecode(search_term)})" 
        data = await self._getRequestJSONData("results", "https://signpuddle.net/puddle/sgn58/sign?term=", search_term)
        return [d["sign"] for d in data]