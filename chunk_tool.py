from typing import Optional
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

def modify_file_chunk(file_path: str, chunk_number: str, new_content: str, vector_store: Optional[Chroma] = None) -> bool:
    """
    Modify a specific chunk of a file and update both the file and the vector store.
    
    Args:
        file_path (str): Path to the file containing the chunk
        chunk_number (str): Chunk number in format "index/total"
        new_content (str): New content for the chunk
        vector_store (Optional[Chroma]): Vector store instance, if None will create new one
        
    Returns:
        bool: True if modification was successful, False otherwise
    """
    try:
        # Initialize vector store if not provided
        if vector_store is None:
            vector_store = Chroma(collection_name="repo")
            
        # Retrieve all chunks for the file
        results = vector_store.get(
            where={"file_path": file_path},
            include=["metadatas", "documents"]
        )
        
        if not results["ids"]:
            return False
            
        # Find the specific chunk
        chunk_docs = []
        target_chunk_index = None
        for i, metadata in enumerate(results["metadatas"]):
            if metadata["chunk_number"] == chunk_number:
                target_chunk_index = i
                
        if target_chunk_index is None:
            return False
            
        # Read the entire file
        with open(file_path, 'r') as f:
            full_content = f.read()
            
        # Split the content into chunks using the same settings as the original
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=3000,
            chunk_overlap=200,
        )
        chunks = text_splitter.split_text(full_content)
        
        # Validate chunk number format
        try:
            index, total = map(int, chunk_number.split('/'))
            if index < 1 or index > total or total != len(chunks):
                return False
        except ValueError:
            return False
            
        # Replace the chunk content
        chunks[index - 1] = new_content
        
        # Join chunks back together
        modified_content = "".join(chunks)
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(modified_content)
            
        # Update vector store
        # Remove old document
        vector_store.delete(
            where={"file_path": file_path, "chunk_number": chunk_number}
        )
        
        # Add new document
        new_doc = Document(
            page_content=new_content,
            metadata={"file_path": file_path, "chunk_number": chunk_number}
        )
        vector_store.add_documents([new_doc])
        
        return True
        
    except Exception as e:
        print(f"Error modifying chunk: {str(e)}")
        return False