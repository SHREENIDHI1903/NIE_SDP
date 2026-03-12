import os
import json

# --- Configuration ---
DATA_PATH = r"D:\NIE_GENai\Capstone_Project\NewsNexus\data\raw_pdfs"
DB_PATH = r"D:\NIE_GENai\Capstone_Project\NewsNexus\data\chroma_db"
PROGRESS_FILE = os.path.join(DB_PATH, "ingestion_progress.json")

def get_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"processed_chunks": 0, "total_chunks": 0, "is_complete": False}

def save_progress(processed, total, complete=False):
    os.makedirs(DB_PATH, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"processed_chunks": processed, "total_chunks": total, "is_complete": complete}, f)

def ingest_documents(progress_callback=None, resume=True):
    from langchain_community.document_loaders import PyPDFDirectoryLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_chroma import Chroma
    # 1. Load Documents
    print(f"Loading PDFs from {DATA_PATH}...")
    loader = PyPDFDirectoryLoader(DATA_PATH)
    raw_documents = loader.load()
    print(f"Loaded {len(raw_documents)} pages.")
    
    # 2. Split Text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
    )
    chunks = text_splitter.split_documents(raw_documents)
    total_chunks = len(chunks)
    print(f"Total chunks to process: {total_chunks}")

    # 3. Resume Logic
    start_chunk = 0
    if resume:
        prog = get_progress()
        if prog["total_chunks"] == total_chunks and not prog["is_complete"]:
            start_chunk = prog["processed_chunks"]
            print(f"Resuming from chunk {start_chunk}...")

    # 4. Initialize Embeddings & Vector Store
    from langchain_ollama import OllamaEmbeddings
    embedding_model = OllamaEmbeddings(model="nomic-embed-text")
    
    vector_db = Chroma(
        embedding_function=embedding_model,
        persist_directory=DB_PATH
    )

    # 5. Micro-Batching (10 chunks for extreme stability)
    BATCH_SIZE = 10
    import time
    import gc

    total_batches = (total_chunks - start_chunk - 1) // BATCH_SIZE + 1
    
    if progress_callback: progress_callback(0.3 if start_chunk == 0 else (start_chunk/total_chunks), f"Starting from chunk {start_chunk}...")

    for i in range(start_chunk, total_chunks, BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        batch_num = (i - start_chunk) // BATCH_SIZE + 1
        
        current_chunk_count = i + len(batch)
        msg = f"Progress: {current_chunk_count}/{total_chunks} chunks..."
        print(f"   > {msg}")
        
        try:
            vector_db.add_documents(batch)
            save_progress(current_chunk_count, total_chunks, complete=(current_chunk_count == total_chunks))
        except Exception as e:
            print(f"   ! Error at chunk {i}: {e}")
            raise e

        if progress_callback:
            progress = 0.3 + (current_chunk_count / total_chunks) * 0.7
            progress_callback(min(progress, 1.0), msg)
        
        gc.collect()
        time.sleep(0.3)
    
    print("Vector Store updated successfully.")
    return len(raw_documents), total_chunks

if __name__ == "__main__":
    # Ensure directory exists
    os.makedirs(DATA_PATH, exist_ok=True)
    
    # Create a dummy PDF if none exists (for testing)
    if not os.path.exists(DATA_PATH) or not os.listdir(DATA_PATH):
        print(f"No PDFs found in {DATA_PATH}. Please add files to enable RAG features.")
    else:
        ingest_documents()