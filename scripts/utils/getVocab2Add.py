import os
import re
from pathlib import Path

vocab_filepath = "./vocab2add.txt"

def getVocab2Add() -> list[str]:
    vocab_list = []
    if not os.path.isfile(vocab_filepath):
        open(vocab_filepath, "w").close()
    
    with open(vocab_filepath, "rb") as f:
        for line in f:
            try:
                word = line.decode()
                vocab_list.append(re.sub(r'(\r|\n)', '', word))
            except UnicodeDecodeError:
                pass
    return vocab_list

def clearVocab2Add():
    Path(vocab_filepath).touch()