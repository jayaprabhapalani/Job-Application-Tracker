from fastembed import TextEmbedding

_model = TextEmbedding("BAAI/bge-small-en-v1.5")


def get_embedding(text: str) -> list[float]:
    return list(_model.embed([text]))[0].tolist()
