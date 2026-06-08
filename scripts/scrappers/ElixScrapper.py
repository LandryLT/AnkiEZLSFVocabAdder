from scripts.scrappers.Scrapper import Scrapper
from scripts.scrappers.ScrapperResults import ElixMeanings, ElixResult
from scripts.caching.cacheSearch import SearchCache
import subprocess
from uuid import uuid4
import os

elix_cache = SearchCache("./cache/elix")
download_folder = "./cache/vids/src/"
convert_folder = "./cache/vids/cnv/"
class ElixScrapper(Scrapper):
    def __init__(self, session):
        super().__init__(session)

    async def searchWord(self, search_term: str) -> ElixResult:
        self.logger.info(f"Searching Elix.fr for {search_term}")
        result = await self.__queryWord(await self.__searchWord(search_term))
        new_meanings = []
        for m in result.meanings:
            new_sign_urls = []
            for sign_url in m.word_signs_urls:
                new_sign_urls.append(await self.__downloadVideo(sign_url, search_term))
            new_def_urls = []
            for def_url in m.def_signs_urls:
                new_def_urls.append(await self.__downloadVideo(def_url, search_term))
            new_meanings.append(ElixMeanings(m.definition, new_sign_urls, new_def_urls))
        return result._replace(meanings=new_meanings)

    async def __downloadVideo(self, url:str, search_term:str):
        f_name = f"{search_term}_{uuid4()}"
        download_path = download_folder + f"{f_name}.mp4"
        output_path = convert_folder + f"{f_name}.webm"
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            with open(download_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 64):
                    f.write(chunk)
        self.__convertVideo(download_path, output_path)
        return output_path
    
    def __convertVideo(self, in_path: str, out_path: str):
        subprocess.run([
        "./ffmpeg/bin/ffmpeg.exe", 
        "-hide_banner", "-loglevel error",
        "-i", in_path,
        "-c:v", "libvpx",
        "-crf", "10",
        "-b:v", "8M",
        "-c:a", "libvorbis",
        out_path
    ], check=True)

    async def __searchWord(self, search_term: str) -> str:
        self.logger.debug(f"Checking search term for {search_term}")
        data = (await self._getJSONData("data", "https://api.elix-lsf.fr/suggests?q=", search_term, "&limit=10&fuzzy=1"))[0]
        return data

    async def __queryWord(self, word: str) -> ElixResult:
        self.logger.debug(f"Getting data for {word}")
        data = (await self._getJSONData("data", "https://api.elix-lsf.fr/words?q=", word))[0]
        meanings = []
        for m in data["meanings"]:
            meanings.append(ElixMeanings(m["definition"], [ws["uri"] for ws in m["wordSigns"]], [ws["uri"] for ws in m["definitionSigns"]]))

        return ElixResult(data["name"], data["typology"], meanings)

    @staticmethod
    def clearCache():
        for f in os.listdir(download_folder):
            os.remove(download_folder+f)
        for f in os.listdir(convert_folder):
            os.remove(convert_folder+f)
        elix_cache.clearCache()
            
    