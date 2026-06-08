from typing import NamedTuple

class ElixMeanings(NamedTuple):
    definition: str
    word_signs_urls: list[str]
    def_signs_urls: list[str]

class ElixResult(NamedTuple):
    gloss: str
    typology: str
    meanings: list[ElixMeanings]

class ScrapperResult(ElixResult):
    sign_writings: list[str]