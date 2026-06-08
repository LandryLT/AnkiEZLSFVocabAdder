from aiohttp import ClientSession
import logging


class Scrapper:
    logger = logging.getLogger(__name__)
    def __init__(self, session: ClientSession):
        self.session = session        
    
    async def _getJSONData(self, data_key:str, pre_query: str, word: str, post_query: str= ""):
        async with self.session.get(pre_query+word+post_query) as resp:
            resp.raise_for_status()
            json_data = await resp.json()
            data = json_data[data_key]
            return data

            