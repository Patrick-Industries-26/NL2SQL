"""
rag/schema_rag.py
─────────────────
Encapsulates the ChromaDB-backed RAG engine that retrieves the most
relevant table schemas for a given natural-language question.
"""

import chromadb
from chromadb.utils import embedding_functions

from config.settings import (
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL_PATH,
    RAG_MAX_DISTANCE,
    RAG_N_RESULTS,
)


class SchemaRAG:
    """Vector-store wrapper for database schema retrieval."""

    def __init__(self) -> None:
        self._client = chromadb.Client()
        self._embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_PATH
        )
        self._collection = self._client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=self._embed_fn,
        )

    # ── Indexing ──────────────────────────────────────────────────────────────

    def index_schema(self, schema_list: list[str]) -> int:
        """
        (Re-)index all table DDL strings.

        Parameters
        ----------
        schema_list : list[str]
            One CREATE TABLE statement per entry.

        Returns
        -------
        int
            Number of documents now in the collection.
        """
        # Clear existing entries
        if self._collection.count() > 0:
            existing_ids = self._collection.get()["ids"]
            self._collection.delete(existing_ids)

        documents, metadatas, ids = [], [], []
        for i, table_def in enumerate(schema_list):
            table_name = table_def.split("TABLE")[1].split("(")[0].strip()
            documents.append(table_def)
            metadatas.append({"table_name": table_name})
            ids.append(f"table_{i}")

        self._collection.add(documents=documents, metadatas=metadatas, ids=ids)
        return self._collection.count()

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def retrieve_relevant_tables(
        self,
        question: str,
        n_results: int = RAG_N_RESULTS,
        max_distance: float = RAG_MAX_DISTANCE,
    ) -> tuple[str, list[str]]:
        """
        Find the *n_results* most relevant table schemas for *question*.

        Returns
        -------
        schema_context : str
            Concatenated DDL strings ready to inject into the LLM prompt.
        table_names : list[str]
            Human-readable names of the retrieved tables.
        """
        results = self._collection.query(
            query_texts=[question],
            n_results=n_results,
            include=["distances", "documents", "metadatas"],
        )

        final_ddl: list[str] = []
        retrieved_tables: list[str] = []

        for i in range(len(results["documents"][0])):
            distance = results["distances"][0][i]
            if distance < max_distance:
                final_ddl.append(results["documents"][0][i])
                retrieved_tables.append(results["metadatas"][0][i]["table_name"])

        return "\n".join(final_ddl), retrieved_tables