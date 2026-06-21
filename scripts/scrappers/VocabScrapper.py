from aiohttp import ClientSession, ClientConnectorError, ClientTimeout
from scripts.scrappers.ElixScrapper import ElixScrapper, elix_cache, video_download_cache
from scripts.scrappers.ScrapperResults import ScrapperResult, ElixResult, SPResult
from scripts.scrappers.SignPuddleScrapper import SignPuddleScrapper, signpuddle_cache
from tqdm.asyncio import tqdm
from scripts.utils.printingUtils import tqdm_format, clearConsole, grey, italic
from scripts.caching.cacheSearch import SearchCache
import functools
from typing import Callable, Any, Coroutine
import asyncio
from asyncio import Semaphore
from asyncio.exceptions import TimeoutError
# from types import CoroutineType

def cacheable(cache: SearchCache):
    def wrapper(f):
        @functools.wraps(f)
        async def wrap(*args, **kwargs):
            try:
                output = await f(*args, **kwargs)
            # except Scrapper.Oops as e:
            #     raise e
            except Exception as e:
                cache.save_pickled_cache()
                raise e
            cache.save_pickled_cache()
            return output
        return wrap
    return wrapper

def errorable(*error_types):
    def wrapper(f):
        @functools.wraps(f)
        async def wrap(*args, **kwargs):
            counter = 0
            while True:
                try:
                    if counter > 0:
                        clearConsole()
                        print(grey(f"Retry counter: {counter}"))
                    output = await f(*args, **kwargs)
                    return output
                except error_types:
                    counter += 1
                except Exception as e:
                    raise e
        return wrap
    return wrapper

class VocabScrapper():
    def __init__(self):
        pass

    async def searchTerms(self, vocab_list: list[str]):
        elix_sem = Semaphore(10)
        clearConsole()
        elix_results = await self._elixSearch(vocab_list, elix_sem)
        elix_downloads_sem = Semaphore(10)
        clearConsole()
        dwnl_elix_results = await self._downloadVideos(elix_results, elix_downloads_sem)
        sp_sem = Semaphore(1)
        clearConsole()
        sp_results = await self._SPSearch(dwnl_elix_results, sp_sem)
        clearConsole()

        output = []
        for elix, spud in zip(dwnl_elix_results, [sp.sign_writings for sp in sp_results]):
            new_sr = ScrapperResult(**elix._asdict())
            new_sr.sign_writings = spud
            all_vids = []
            no_rez = []
            for m in elix.meanings:
                all_vids += m.word_signs_url
            if spud or all_vids:
                output.append(new_sr)
            else:
                no_rez.append(new_sr)
        return output, no_rez

    @errorable(TimeoutError, ClientConnectorError)
    @cacheable(elix_cache)
    async def _elixSearch(self, vocab_list: list[str], sem: Semaphore) -> list[ElixResult]:
        search_results = []
        prepare_output: Callable[[list[ElixResult], list[str]], None] = lambda rez, stl: search_results.append(rez) if rez and rez[0].gloss in stl else True
        async def callback(st: str, rez=None) -> None:
            async with sem:
                rez = await self.elix_scrap.searchWord(st)
                search_results.append(rez)
                return rez
        (uncached_vocab_list, search_results, cache_on_append_result) = self.fromcache(elix_cache, vocab_list, callback, prepare_output, search_results, True)
        print("Searching "+ italic("elix-lsf.fr..."))
        elix_co = [asyncio.ensure_future(cache_on_append_result(search_term=wrd, rez=None)) for wrd in uncached_vocab_list]
        await tqdm.gather(*elix_co, bar_format=tqdm_format, leave=False, total=len(vocab_list), initial=len(vocab_list)-len(uncached_vocab_list))
        output = [o for out in search_results for o in out]
        return [o for o in output if o]

    @errorable(TimeoutError, ClientConnectorError)
    @cacheable(signpuddle_cache)
    async def _SPSearch(self, vocab_list: list[ElixResult], sem: Semaphore) -> list[SPResult]:
        output = []
        prepare_output: Callable[[SPResult, list[str]], None] = lambda rez, stl: output.append(rez) if rez.gloss in stl else True
        async def callback(st: str, rez=None) -> None:
            async with sem:
                rez = await self.signpuddle_scrap.getSVG(st)
                output.append(rez)
                return rez
        (uncached_vocab_list, output, cache_on_append_result) = self.fromcache(signpuddle_cache, [rez.gloss for rez in vocab_list], callback, prepare_output, output, True)
        print("Searching "+ italic("signpuddle.net..."))
        signpuddle_co = [asyncio.ensure_future(cache_on_append_result(search_term=er, rez=None)) for er in uncached_vocab_list]
        await tqdm.gather(*signpuddle_co, bar_format=tqdm_format, leave=False, total=len(vocab_list), initial=len(vocab_list)-len(uncached_vocab_list))
        return output

    @errorable(TimeoutError, ClientConnectorError)
    @cacheable(video_download_cache)
    async def _downloadVideos(self, vocab_list: list[ElixResult], sem: Semaphore) -> list[ElixResult]:
        output = []
        def prepare_output(rez: ElixResult, stl: list[str]) -> None: 
            if rez.gloss in stl:
                output.append(rez) 
        async def callback(st: str, rez=ElixResult) -> None:
            rez = await self.elix_scrap.downloadVideos(rez, sem)
            output.append(rez)
            return rez
        (uncached_vocab_list, output, cache_on_append_result) = self.fromcache(video_download_cache, [rez.gloss for rez in vocab_list], callback, prepare_output, output, True)
        uncached_vocab_list = [er for er in vocab_list if er.gloss in uncached_vocab_list]
        print("Downloading and converting videos from "+ italic("elix-lsf.fr..."))
        downloads_co = [asyncio.ensure_future(cache_on_append_result(search_term=er.gloss, rez=er)) for er in uncached_vocab_list]
        await tqdm.gather(*downloads_co, bar_format=tqdm_format, leave=False, total=len(vocab_list), initial=len(vocab_list)-len(uncached_vocab_list))
        return output

    async def __aenter__(self):
        self.session = ClientSession(timeout=ClientTimeout(60))
        self.elix_scrap = ElixScrapper(self.session)
        self.signpuddle_scrap = SignPuddleScrapper(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()
    
    def fromcache(self, cache: SearchCache, search_terms: list[str], callback: Callable[[Any], None] | None = None,  prepare_output_func: Callable[[Any, list[str]], None] | None = None, output_buffer: list = [], is_coroutine = False) -> tuple[list[str], list[Any], Callable[[str, Any], None] | Coroutine[Any, Any, Any]]:
        cache_data = cache.cache
        cached_search = [cached_data for key, cached_data in cache_data.items() if key in search_terms]        
        cached_objects = output_buffer
        for csgroup in cached_search:
            for cs in csgroup:
                if prepare_output_func:
                    prepare_output_func(cs, search_terms)
                    # output.append(cs)
        # [[output.append(cs) for cs in csgroup] for csgroup in cached_search]
        uncached_search_terms = [st for st in search_terms if not st in cache_data.keys()]
        # callback = cached_objects.append if callback is None else callback 
        if is_coroutine:
            async def on_append_result(search_term: str, rez: Any):
                if callback:
                    rez = await callback(search_term, rez)
                cache.addToCache(search_term, rez)
        else:
            def on_append_result(search_term: str, rez: Any):
                if callback:
                    rez = callback(search_term, rez)
                cache.addToCache(search_term, rez)
        return (uncached_search_terms, cached_objects, on_append_result)
