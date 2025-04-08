import os
import pinecone
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

def initialize_pinecone():
    pc = Pinecone(
        api_key=os.getenv('PINECONE_API_KEY')
    )
    
    index_name = "helix"
    if index_name not in pc.list_indexes():
        pc.create_index(
            name=index_name,
            dimension=1536, 
            metric="cosine"
        )
    
    return pc.Index(index_name)

def store_hr_knowledge(index, texts, metadatas=None):
    """
    Store HR knowledge in Pinecone
    """
    pass

def query_hr_knowledge(index, query, top_k=5):
    """
    Query HR knowledge from Pinecone
    """
    pass
