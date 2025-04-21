import os
from dotenv import load_dotenv
from pinecone import Pinecone
from enum import Enum

# Load environment variables
load_dotenv()

# Initialize Pinecone client
pc = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment=os.getenv("PINECONE_ENVIRONMENT")
)

# Define the index name
INDEX_NAME = "helia-chat-kb"

# Connect to the index
index = pc.Index(INDEX_NAME)

class BotNamespace(Enum):
    SUN_SHIELD = "sun-shield"
    GROWTH_RAY = "growth-ray"
    SUNBEAM = "sunbeam"
    INNER_DAWN = "inner-dawn"

    @classmethod
    def get_display_name(cls, bot):
        return {
            cls.SUN_SHIELD: "Helia Sun Shield",
            cls.GROWTH_RAY: "Helia Growth Ray",
            cls.SUNBEAM: "Helia Sunbeam",
            cls.INNER_DAWN: "Helia Inner Dawn"
        }.get(bot, bot.name)

    @classmethod
    def values(cls):
        return [bot.value for bot in cls]

def embed_texts(texts: list[str], input_type: str) -> list[list[float]]:
    if input_type not in ("passage", "query"):
        raise ValueError("input_type must be 'passage' or 'query'")

    # Pass input_type inside parameters, not as a top‑level arg
    response = pc.inference.embed(
        model="llama-text-embed-v2",
        inputs=texts,
        parameters={"input_type": input_type}
    )
    # response is a list of dicts like {"id":..., "values":[...]}
    return [item["values"] for item in response]

def upsert_text(texts: list[str], metadata: list[dict], bot: str) -> int:
    if bot not in BotNamespace.values():
        raise ValueError(f"Invalid bot name: {bot}. Must be one of {BotNamespace.values()}")

    # 1) Generate embeddings for passages
    embeddings = embed_texts(texts, input_type="passage")

    # 2) Build the vectors payload
    vectors = [
        (str(i), embedding, {**meta, "text": text})
        for i, (text, embedding, meta) in enumerate(zip(texts, embeddings, metadata))
    ]

    # 3) Upsert into Pinecone
    resp = index.upsert(vectors=vectors, namespace=bot)
    return resp["upserted_count"]

def query_text(query: str, bot: str, top_k: int = 5) -> list[dict]:
    if bot not in BotNamespace.values():
        raise ValueError(f"Invalid bot name: {bot}. Must be one of {BotNamespace.values()}")

    # 1) Embed the query
    query_vec = embed_texts([query], input_type="query")[0]

    # 2) Query the index
    result = index.query(
        vector=query_vec,
        top_k=top_k,
        namespace=bot,
        include_metadata=True
    )

    # 3) Format and return matches
    return [
        {
            "id": match["id"],
            "text": match["metadata"].get("text", ""),
            "score": match["score"]
        }
        for match in result.get("matches", [])
    ]