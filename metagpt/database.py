from pinecone import Pinecone
from metagpt.config import CONFIG


class Database:
    def __init__(self):
        self.config = CONFIG
        self.init_db()

    def init_db(self):
        PINECONE_API_KEY = "01b08fa6-3316-4941-9a89-5de66530c7ef"
        self.pc = Pinecone(api_key=PINECONE_API_KEY)

    async def ask_ab(self, emb: list[float], idx_name: str, top_k: int):
        index = self.pc.Index(idx_name)
        infos = index.query(vector=emb, top_k=top_k, include_metadata=True)
        res = []
        for info in infos['matches']:
            res.append(info['metadata'])

        return res
        
    
    