"""
轻量级 Chroma 测试替身。

用于在无网络、无真实 Chroma Cloud 的测试环境中提供最小可用行为。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from typing import Any


def _matches_where(metadata: dict[str, Any], where: dict[str, Any] | None) -> bool:
    if not where:
        return True

    if "$and" in where:
        return all(_matches_where(metadata, clause) for clause in where["$and"])

    if "$or" in where:
        return any(_matches_where(metadata, clause) for clause in where["$or"])

    for key, expected in where.items():
        actual = metadata.get(key)
        if isinstance(expected, dict):
            if "$in" in expected and actual not in expected["$in"]:
                return False
            if "$ne" in expected and actual == expected["$ne"]:
                return False
        elif actual != expected:
            return False

    return True


def _cosine_distance(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 1.0

    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))

    if left_norm == 0 or right_norm == 0:
        return 1.0

    similarity = dot / (left_norm * right_norm)
    similarity = max(min(similarity, 1.0), -1.0)
    return 1.0 - similarity


@dataclass
class FakeChromaRecord:
    record_id: str
    document: str
    metadata: dict[str, Any]
    embedding: list[float]


@dataclass
class FakeChromaCollection:
    name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    _records: dict[str, FakeChromaRecord] = field(default_factory=dict)

    def count(self) -> int:
        return len(self._records)

    def peek(self, limit: int = 1) -> dict[str, list[Any]]:
        return self.get(limit=limit)

    def add(
        self,
        *,
        embeddings: list[list[float]],
        ids: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        documents: list[str] | None = None,
    ) -> None:
        metadatas = metadatas or [{} for _ in ids]
        documents = documents or ["" for _ in ids]

        for record_id, document, metadata, embedding in zip(
            ids,
            documents,
            metadatas,
            embeddings,
            strict=True,
        ):
            self._records[record_id] = FakeChromaRecord(
                record_id=record_id,
                document=document,
                metadata=dict(metadata or {}),
                embedding=list(embedding or []),
            )

    def update(
        self,
        *,
        ids: list[str],
        embeddings: list[list[float]] | None = None,
        metadatas: list[dict[str, Any]] | None = None,
        documents: list[str] | None = None,
    ) -> None:
        embeddings = embeddings or [[] for _ in ids]
        metadatas = metadatas or [{} for _ in ids]
        documents = documents or ["" for _ in ids]

        for record_id, document, metadata, embedding in zip(
            ids,
            documents,
            metadatas,
            embeddings,
            strict=True,
        ):
            if record_id not in self._records:
                continue
            record = self._records[record_id]
            if document:
                record.document = document
            if metadata:
                record.metadata.update(metadata)
            if embedding:
                record.embedding = list(embedding)

    def delete(
        self,
        *,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
    ) -> None:
        if ids:
            for record_id in ids:
                self._records.pop(record_id, None)
            return

        if where:
            to_delete = [
                record_id
                for record_id, record in self._records.items()
                if _matches_where(record.metadata, where)
            ]
            for record_id in to_delete:
                self._records.pop(record_id, None)

    def get(
        self,
        *,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
        limit: int | None = None,
        **_: Any,
    ) -> dict[str, list[Any]]:
        records = self._filtered_records(ids=ids, where=where)
        if limit is not None:
            records = records[:limit]

        return {
            "ids": [record.record_id for record in records],
            "documents": [record.document for record in records],
            "metadatas": [record.metadata for record in records],
            "embeddings": [record.embedding for record in records],
        }

    def query(
        self,
        *,
        query_embeddings: list[float] | list[list[float]],
        n_results: int,
        where: dict[str, Any] | None = None,
        **_: Any,
    ) -> dict[str, list[list[Any]]]:
        queries = query_embeddings
        if queries and isinstance(queries[0], (int, float)):
            queries = [queries]  # type: ignore[list-item]

        filtered = self._filtered_records(ids=None, where=where)
        result_ids: list[list[str]] = []
        result_documents: list[list[str]] = []
        result_metadatas: list[list[dict[str, Any]]] = []
        result_distances: list[list[float]] = []

        for query_embedding in queries:  # type: ignore[assignment]
            ranked = sorted(
                filtered,
                key=lambda record: _cosine_distance(list(query_embedding), record.embedding),
            )[:n_results]
            result_ids.append([record.record_id for record in ranked])
            result_documents.append([record.document for record in ranked])
            result_metadatas.append([record.metadata for record in ranked])
            result_distances.append(
                [_cosine_distance(list(query_embedding), record.embedding) for record in ranked]
            )

        return {
            "ids": result_ids,
            "documents": result_documents,
            "metadatas": result_metadatas,
            "distances": result_distances,
        }

    def _filtered_records(
        self,
        *,
        ids: list[str] | None,
        where: dict[str, Any] | None,
    ) -> list[FakeChromaRecord]:
        records = list(self._records.values())
        if ids is not None:
            allowed = set(ids)
            records = [record for record in records if record.record_id in allowed]
        if where:
            records = [record for record in records if _matches_where(record.metadata, where)]
        return records


class FakeChromaClient:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        self._collections: dict[str, FakeChromaCollection] = {}

    def get_or_create_collection(
        self,
        *,
        name: str,
        metadata: dict[str, Any] | None = None,
        **_kwargs: Any,
    ) -> FakeChromaCollection:
        if name not in self._collections:
            self._collections[name] = FakeChromaCollection(name=name, metadata=metadata or {})
        return self._collections[name]

    def get_collection(self, name: str, **_kwargs: Any) -> FakeChromaCollection:
        return self.get_or_create_collection(name=name)

    def list_collections(self) -> list[FakeChromaCollection]:
        return list(self._collections.values())

    def delete_collection(self, name: str) -> None:
        self._collections.pop(name, None)

    def close(self) -> None:
        self._collections.clear()

    def reset(self) -> None:
        self._collections.clear()
