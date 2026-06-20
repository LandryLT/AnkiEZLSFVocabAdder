from scripts.scrappers.Scrapper import Scrapper
from scripts.scrappers.ScrapperResults import ElixMeanings, ElixResult
from scripts.caching.cacheSearch import SearchCache
import subprocess
from uuid import uuid4
import os
import asyncio
from pathlib import Path
elix_cache = SearchCache(Path("./cache/elix"))
video_download_cache = SearchCache(Path("./cache/video_dnwld"))
download_folder = "./cache/vids/src/"
convert_folder = "./cache/vids/cnv/"

class ElixScrapper(Scrapper):
    def __init__(self, session):
        super().__init__(session)


    async def searchWord(self, search_term: str) -> list[ElixResult | None]:
        self.logger.info(f"Searching Elix.fr for {search_term}")
        rez = await self.__searchWord(search_term)
        if rez:
            return await self.__queryWord(rez)
        else:
            return [None]


    async def downloadVideos(self, result: ElixResult) -> ElixResult:
        download_co = []
        for m in result.meanings:
            for url in m.word_signs_url:
                download_co.append(self.__downloadVideo(url, result.gloss, "sign"))
            download_co.append(self.__downloadVideo(m.def_signs_url, result.gloss, "def")) if m.def_signs_url else None
        downloaded_paths = await asyncio.gather(*download_co)
        new_meanings = []
        for m in result.meanings:
            new_word_sign = []
            for _ in m.word_signs_url:
                new_word_sign.append(downloaded_paths.pop(0))
            new_def_sign = downloaded_paths.pop(0) if m.def_signs_url else None
            new_meanings.append(ElixMeanings(m.definition, new_word_sign, new_def_sign))
        return result._replace(meanings=new_meanings)


    async def __downloadVideo(self, url:str, search_term:str, prefix:str):
        f_name = f"{prefix}_{search_term}_{uuid4()}"
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
            "-hide_banner", "-loglevel", "error",
            "-i", in_path, "-filter:v", "scale=360:-1",
            "-c:v", "libvpx",
            "-crf", "10",
            "-b:v", "8M",
            "-c:a", "libvorbis",
            out_path
        ], check=True)


    async def __searchWord(self, search_term: str) -> str:
        self.logger.debug(f"Checking search term for {search_term}")
        data = (await self._getJSONData("data", "https://api.elix-lsf.fr/suggests?q=", search_term, "&limit=10&fuzzy=1"))
        if data:
            return data[0]
        return None


    async def __queryWord(self, word: str) -> list[ElixResult]:
        self.logger.debug(f"Getting data for {word}")
        data = (await self._getJSONData("data", "https://api.elix-lsf.fr/words?q=", word))
        output = []
        for d in data:
            meanings = []
            if d["name"] == word:
                for m in d["meanings"]:
                    ws = [w["uri"] for w in m["wordSigns"]]
                    ds = None if not m["definitionSigns"] else m["definitionSigns"][0]["uri"]
                    meanings.append(ElixMeanings(m["definition"], ws, ds))
                output.append(ElixResult(d["name"], d["typology"], meanings))

        return output


    @staticmethod
    def clearCache():
        for f in os.listdir(download_folder):
            os.remove(download_folder+f)
        for f in os.listdir(convert_folder):
            os.remove(convert_folder+f)
        elix_cache.clearCache()
        video_download_cache.clearCache()
            
    