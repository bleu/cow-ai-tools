"""Build and save FAISS index from CoW docs + OpenAPI. Run: python -m cow_brains.build_faiss"""
import asyncio
import os

from cow_brains.config import COW_FAISS_PATH, EMBEDDING_MODEL
from cow_brains.data_exporter import DataExporter
from op_brains.chat.apis import access_APIs
from langchain_community.vectorstores import FAISS


async def main():
    print("Loading documents...")
    df = await DataExporter.get_dataframe(only_not_embedded=False)
    documents = df["content"].tolist()
    if not documents:
        print("No documents. Set COW_DOCS_PATH and/or COW_OPENAPI_PATH and ensure artifacts exist.")
        return

    print(f"Embedding {len(documents)} chunks...")
    embeddings = access_APIs.get_embedding(EMBEDDING_MODEL)
    db = FAISS.from_documents(documents, embeddings)

    os.makedirs(COW_FAISS_PATH, exist_ok=True)
    db.save_local(COW_FAISS_PATH)
    print(f"Saved FAISS index to {COW_FAISS_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
