#!/usr/bin/env python3
from typing import Dict, Sequence, Tuple, cast, List
import argparse
from collections import defaultdict
from pathlib import Path
import re
import random
import json

class WordCandidate:
    def __init__(
        self,
        word: str,
        location: Tuple[int, int],
        weight: float,
    ):
        self.word = word
        self.normalized_word = word.lower()
        self.start, self.stop = location
        self.weight = weight


def generate_local_importance_index(corpus: str, weight_overrides: Sequence[Tuple[str, float]]):
    words = [match.group().lower() for match in re.finditer(r'([a-zA-Z\-\']+)', corpus)]
    counts = defaultdict(lambda: 0)
    for word in words:
        counts[word] += 1
    weights = { word: 1/count**2 for word, count in counts.items() }
    for word, weight in weights.items():
        final_weight = weight 
        for (override_pattern, override_weight) in weight_overrides:
            if re.match(override_pattern, word):
                final_weight = override_weight / counts[word]
        if final_weight != weight:
            weights[word] = final_weight
    normalize = 1 / sum(weights.values())
    return {word: weight * normalize for word, weight in weights.items()}


def generate_location_index(corpus: str) -> Dict[str, List[Tuple[int, int]]]:
    locations_index = cast(Dict[str, List[Tuple[int, int]]], defaultdict(lambda: list()))
    for match in re.finditer(r'([a-zA-Z\-\']+)', corpus):
        locations_index[match.group().lower()].append(match.span())
    return locations_index


def sample_word_candidates(word_candidates: Sequence[WordCandidate], number: int) -> Sequence[WordCandidate]:
    return random.choices(word_candidates, weights=[candidate.weight for candidate in word_candidates], k=number)


def main(filename: str, words_to_hide: int, weight_overrides=Sequence[Tuple[str, float]]):
    corpus = Path(filename).read_text()
    location_index = generate_location_index(corpus)
    importance_index = generate_local_importance_index(corpus, weight_overrides=weight_overrides)
    candidates = []
    for (word, locations) in location_index.items():
        candidates += [WordCandidate(word, location, importance_index[word]) for location in locations]
    sampled = sample_word_candidates(candidates, words_to_hide)
    corpus_mut = list(corpus)
    for candidate in sampled:
        for i in range(candidate.start, candidate.stop):
            corpus_mut[i] = '*'
    print("".join(corpus_mut))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("--words-to-hide", type=int, default=10)
    parser.add_argument("--weight-override", type=json.loads, action='append', default=[])
    args = parser.parse_args()
    main(filename=args.filename, words_to_hide=args.words_to_hide, weight_overrides=args.weight_override)

