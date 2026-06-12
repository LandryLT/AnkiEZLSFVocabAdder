from re import match
from pathlib import Path
from scripts.anki.ankiConfig import AnkiConfig, DuplicateRemoveMode

class scrapperConfigParser():
    def __init__(self, filepath: str = "./searchConfig.txt"):
        self.ankiConfig = AnkiConfig(None, DuplicateRemoveMode.NONE)
        self.use_cache = None
        self.delete_cache_on_complete = None
        self.delete_vocablist_on_complete = None
        with open(filepath, 'r') as f:
            lines = [l for l in f.readlines() if not match(r'^\#', l)]
            params = {}
            for l in lines:
                param_match = match(r'(^[^=]+)=(.*$)', l)
                if not param_match:
                    continue
                params[param_match.group(1)] = param_match.group(2)
            
            for key, item in params.items():
                match key:
                    case "use_cache":
                        self.use_cache = self.parseBool(item)
                    case "delete_cache_on_complete":
                        self.delete_cache_on_complete = self.parseBool(item)
                    case "delete_vocablist_on_complete":
                        self.delete_vocablist_on_complete = self.parseBool(item)
                    case "anki_collection_file_path":
                        self.ankiConfig = self.ankiConfig._replace(col_path=self.parsePath(item))
                    case "anki_collection_deduplication":
                        self.ankiConfig = self.ankiConfig._replace(dupl_resolve=self.parseDeduplicationMode(item))

    @staticmethod
    def parseInt(value: str) -> (int | None):
        value = match(r'^\d+$', value)
        if not value:
            return -1
        return int(value.group(0))
    
    @staticmethod
    def parseBool(value: str) -> (bool | None):
        value = match(r'^(YES|NO)$', value)
        if not value:
            return None
        value = value.group(0)
        return value == "YES"
    
    @staticmethod
    def parseDeduplicationMode(value) -> DuplicateRemoveMode:
        value = match(r'^(OLDEST|NEWEST|UPDATE)$', value)
        if not value:
            return DuplicateRemoveMode.NONE
        value = value.group(0)
        return DuplicateRemoveMode(["OLDEST", "NEWEST", "UPDATE"].index(value))

    @staticmethod
    def parsePath(value: str) -> Path:
        value: Path = Path(value)
        if not value.is_file():
            return None
        return value
        