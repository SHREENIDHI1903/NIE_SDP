import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# --- Configuration ---
DATA_PATH = r"D:\NIE_GENai\Capstone_Project\NewsNexus\data\raw_pdfs"
DB_PATH = r"D:\NIE_GENai\Capstone_Project\NewsNexus\data\chroma_db"

def ingest_documents():
    # 1. Load Documents (Day 3: Data Loading)
    print(f"Loading PDFs from {DATA_PATH}...")
    loader = PyPDFDirectoryLoader(DATA_PATH)
    raw_documents = loader.load()
    print(f"Loaded {len(raw_documents)} pages.")

    # 2. Split Text (Day 3: Chunking Strategies)
    # We use overlapping chunks to maintain context across boundaries [cite: 45]
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,      # Balance between context and precision
        chunk_overlap=50,    # Overlap to prevent data loss at edges
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(raw_documents)
    print(f"Split into {len(chunks)} chunks.")

    # 3. Initialize Embeddings (Day 2: Sentence Transformers)
    # Using 'all-MiniLM-L6-v2' which is highly efficient for CPU [cite: 43]
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 4. Create Vector Store (Day 2: Vector Databases)
    print("Creating Vector Store...")
    Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=DB_PATH
    )
    print(f"Success! Vector DB saved to {DB_PATH}")

if __name__ == "__main__":
    # Ensure directory exists
    os.makedirs(DATA_PATH, exist_ok=True)
    
    # Create a dummy PDF if none exists (for testing)
    if not os.listdir(DATA_PATH):
        print(f"Please put a PDF in {DATA_PATH} and run again.")
    else:
        ingest_documents()