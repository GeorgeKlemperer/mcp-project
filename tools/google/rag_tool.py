# RAG tool - wip: read-only file system error

import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from typing import Optional
from pydantic import BaseModel, Field

load_dotenv()

class RAGResponse(BaseModel):
    answer: str = Field(..., description="The generated answer based on retrieved documents")
    sources: list[str] = Field(..., description="List of source documents used")
    confidence: float = Field(..., description="Confidence score for the answer")

class RAGTool:
    def __init__(self):
        self.openai = OpenAI()
        # Use absolute path to project root for chroma_db
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.db_path = os.path.join(project_root, "chroma_db")   

    def query_documents(self, query: str, max_results: int = 5) -> RAGResponse:
        """
        Query the RAG document collection to get relevant information.
        
        Args:
            query (str): The question or query to search for
            max_results (int): Maximum number of relevant chunks to retrieve
            
        Returns:
            RAGResponse: Generated answer with sources and confidence
        """
        try:
            # Connect to ChromaDB
            db = chromadb.PersistentClient(path=self.db_path)
            collection = db.get_collection("rag-documents")
            
            # Embed the query
            query_response = self.openai.embeddings.create(
                input=[query], 
                model="text-embedding-3-small"
            )
            query_embedding = query_response.data[0].embedding
            
            # Search for relevant chunks
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results
            )
            
            if not results['documents'][0]:
                return RAGResponse(
                    answer="I couldn't find any relevant information for your query.",
                    sources=[],
                    confidence=0.0
                )
            
            # Combine retrieved chunks
            context = "\n\n".join(results['documents'][0])
            sources = list(set([meta['source'] for meta in results['metadatas'][0]]))
            
            # Generate answer using GPT
            completion = self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant. Answer the user's question based on the provided context. If the context doesn't contain relevant information, say so clearly."
                    },
                    {
                        "role": "user", 
                        "content": f"Context:\n{context}\n\nQuestion: {query}"
                    }
                ],
                temperature=0.1
            )
            
            answer = completion.choices[0].message.content
            confidence = min(results['distances'][0]) if results['distances'][0] else 1.0
            confidence = max(0.0, 1.0 - confidence)  # Convert distance to confidence
            
            return RAGResponse(
                answer=answer,
                sources=sources,
                confidence=confidence
            )
            
        except Exception as e:
            return RAGResponse(
                answer=f"Error querying documents: {str(e)}",
                sources=[],
                confidence=0.0
            )

    # def refresh_documents(self) -> dict:
    #     """
    #     Re-ingest all documents from the rag-documents folder.
        
    #     Returns:
    #         dict: Status of the refresh operation
    #     """
    #     try:
    #         # Import and run the ingestion process
    #         from .ingest import load_and_chunk, embed_and_store
            
    #         project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    #         documents_dir = os.path.join(project_root, "tools", "google", "rag-documents")

    #         chunks = load_and_chunk(documents_dir)
    #         embed_and_store(chunks)
            
    #         return {
    #             "status": "success",
    #             "message": f"Successfully refreshed {len(chunks)} chunks",
    #             "chunks_count": len(chunks)
    #         }
    #     except Exception as e:
    #         return {
    #             "status": "error",
    #             "message": f"Error refreshing documents: {str(e)}",
    #             "chunks_count": 0
    #         }

    def refresh_documents(self) -> dict:
        """
        Re-ingest all documents from the rag-documents folder.
        Note: Due to filesystem restrictions in MCP environment, 
        please run 'python ./tools/google/ingest.py' manually to refresh.
        """
        return {
            "status": "info",
            "message": "Please run 'python ./tools/google/ingest.py' manually from your terminal to refresh the knowledge base. The MCP environment has filesystem restrictions.",
            "chunks_count": 0
        }
