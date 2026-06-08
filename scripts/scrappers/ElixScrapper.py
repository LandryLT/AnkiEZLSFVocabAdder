from scripts.scrappers.Scrapper import Scrapper
from scripts.scrappers.ScrapperResults import ElixMeanings, ElixResult
class ElixScrapper(Scrapper):
    def __init__(self, session):
        super().__init__(session)

    async def searchWord(self, search_term: str) -> ElixResult:
        return await self.__queryWord(await self.__searchWord(search_term))

    async def __searchWord(self, search_term: str) -> str:
        data = (await self._getRequestJSONData("data", "https://api.elix-lsf.fr/suggests?q=", search_term, "&limit=10&fuzzy=1"))[0]
        return data

    async def __queryWord(self, word: str) -> ElixResult:
        data = (await self._getRequestJSONData("data", "https://api.elix-lsf.fr/words?q=", word))[0]
        meanings = []
        for m in data["meanings"]:
            meanings.append(ElixMeanings(m["definition"], [ws["uri"] for ws in m["wordSigns"]], [ws["uri"] for ws in m["definitionSigns"]]))

        return ElixResult(data["name"], data["typology"], meanings)
            
    