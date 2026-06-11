from typing import NamedTuple

class ElixMeanings(NamedTuple):
    definition: str
    word_signs_url: list[str]
    def_signs_url: str | None

class ElixResult(NamedTuple):
    gloss: str
    typology: str
    meanings: list[ElixMeanings]

class SPPreResult(NamedTuple):
    gloss: str
    sign: list[str]
    
class SPResult(NamedTuple):
    gloss: str
    sign_writings: list[str]

class ScrapperResult(ElixResult):
    sign_writings: list[str]