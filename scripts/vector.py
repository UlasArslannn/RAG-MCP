from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os 
import pandas as pd


path = "reviews_montagna_20260204_220144.csv"

df = pd.read_csv(path)

embeddings = OllamaEmbeddings(model="mxbai-embed-large")

db_location = "./chroma_langchain_db"

add_documents = not os.path.exists(db_location)


if add_documents:

    documents = []
    ids = []

    for i, row in df.iterrows():
        document = Document(
            page_content=row['username'] +  " " + row['text'],
            metadata={
                "id": row['id'],
                "username": row['username'],
                "rating": row['rating']
            },
            id=str(i)
        )
        documents.append(document)
        ids.append(str(i))


vector_store = Chroma(
    collection_name="reviews_montagna",
    embedding_function=embeddings,
    persist_directory=db_location
)


if add_documents:
    vector_store.add_documents(documents=documents, ids=ids)


retriever = vector_store.as_retriever(
    search_kwargs={
        "k": 60
    }
)
