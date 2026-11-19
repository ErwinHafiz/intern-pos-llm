"""Mencocokkan nama longgar dari user ("uu pdp", "paper lightrag") ke dataset/dokumen asli.

Urutan: sama persis → substring kata utuh → singkatan/token → typo (difflib).
Lebih dari satu kandidat sama kuat = ambigu → kembalikan kandidat, jangan menebak.
"""

import difflib
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

from smart_library.backends.base import RagBackend

STOPWORDS = {"dataset", "dokumen", "file", "paper", "the", "a", "an", "of", "tentang", "dan", "atas"}


@dataclass
class Target:
    kind: Literal["dataset", "document"]
    id: str
    label: str
    dataset_id: str


def _norm(s: str) -> str:
    s = re.sub(r"\.(pdf|docx?|xlsx?|pptx?|md|txt|csv|html?)$", "", s.strip().lower())
    words = re.sub(r"[^a-z0-9]+", " ", s).split()
    return " ".join(w for w in words if w not in STOPWORDS)


def _tokens(label: str) -> set[str]:
    """Kata + singkatan dari 2–4 kata berurutan ('pelindungan data pribadi' → 'pdp')."""
    words = _norm(label).split()
    alpha = [w for w in words if w.isalpha()]
    acronyms = {"".join(w[0] for w in alpha[i:i + n]) for n in (2, 3, 4) for i in range(len(alpha) - n + 1)}
    return set(words) | acronyms


def _candidates(backend: RagBackend) -> list[Target]:
    out = []
    for ds in backend.list_datasets():
        out.append(Target("dataset", ds.id, ds.name, ds.id))
        out += [Target("document", d.id, d.name, ds.id) for d in backend.list_documents(ds.id)]
    return out


def _match(query: str, cands: list[Target]) -> tuple[list[Target], bool]:
    """(kandidat, exact). exact=True hanya bila nama ternormalisasi sama persis."""
    q = _norm(query)
    if not q:
        return [], False
    exact = [t for t in cands if _norm(t.label) == q]
    if exact:
        return exact, True
    stages = [
        lambda t: f" {q} " in f" {_norm(t.label)} ",  # substring per kata utuh ("ai" ≠ "lain")
        lambda t: set(q.split()) <= _tokens(t.label),
    ]
    for stage in stages:
        hits = [t for t in cands if stage(t)]
        if hits:
            return hits, False
    # typo: semua target dengan kunci yang mirip ikut dikembalikan (seri = ambigu, bukan dipilih diam-diam)
    by_norm = defaultdict(list)
    for t in cands:
        by_norm[_norm(t.label)].append(t)
    close = difflib.get_close_matches(q, by_norm, n=3, cutoff=0.6)
    if not close:  # typo pada satu kata panjang ("lightrga") dicocokkan per kata judul
        by_norm = defaultdict(list)
        for t in cands:
            for w in set(_norm(t.label).split()):
                if len(w) > 4:
                    by_norm[w].append(t)
        close = difflib.get_close_matches(q, by_norm, n=3, cutoff=0.75)
    hits = {id(t): t for key in close for t in by_norm[key]}
    return list(hits.values()), False


def resolve_names(backend: RagBackend, names: list[str]) -> tuple[list[Target], dict[str, list[str]]]:
    cands = _candidates(backend)
    resolved, unresolved = [], {}
    for name in names:
        hits, _ = _match(name, cands)
        if len(hits) == 1:
            resolved.append(hits[0])
        else:
            unresolved[name] = [t.label for t in hits]
    return resolved, unresolved


def resolve_one(backend: RagBackend, name: str, kind: str | None = None,
                strict: bool = False) -> tuple[Target | None, list[str]]:
    """Satu nama → (Target, []) atau (None, kandidat). `kind` membatasi ke dataset/document.

    strict=True: hanya nama yang sama persis (abaikan huruf besar/kecil) yang diterima; kecocokan
    longgar dikembalikan sebagai kandidat. Dipakai saat salah tebak merugikan (upload ke dataset).
    """
    cands = [t for t in _candidates(backend) if kind is None or t.kind == kind]
    hits, exact = _match(name, cands)
    if len(hits) == 1 and (exact or not strict):
        return hits[0], []
    return None, [t.label for t in hits]
