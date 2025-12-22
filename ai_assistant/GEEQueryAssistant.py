import os
import time
import json
from tqdm import tqdm 
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

load_dotenv()
# Also try loading from the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

print(f"DEBUG: NVIDIA_API_KEY present: {'NVIDIA_API_KEY' in os.environ}")
print(f"DEBUG: HF_TOKEN present: {'HF_TOKEN' in os.environ}")


class GEEQueryAssistant:
    def __init__(self, json_path: str, persist_directory: str = "./chroma_db"):
        self.json_path = json_path
        self.persist_directory = persist_directory
        
        # self.embedding_model = OllamaEmbeddings(model='nomic-embed-text:latest')
        self.embedding_model = NVIDIAEmbeddings(
            model="nvidia/nv-embed-v1", 
            api_key=os.environ.get("NVIDIA_API_KEY"),
            truncate="END"
        )
        
        # Allow model selection via env var, default to Qwen 32B Coder
        model_name = os.environ.get("HF_MODEL", "Qwen/Qwen2.5-Coder-32B-Instruct")
        print(f"DEBUG: Using HF Model: {model_name}")
        
        self.llm = ChatOpenAI(
            model=model_name, 
            openai_api_key=os.environ["HF_TOKEN"],
            openai_api_base="https://router.huggingface.co/v1",
            temperature=0.0
        )
        
        self._validate_db_compatibility()
        self.vector_store = self._load_vector_store()
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity", 
            search_kwargs={"k": 10}
        )
        
        # ADD THIS DEBUG LINE:
        try:
            count = self.vector_store._collection.count()
            print(f"✅ VECTOR DB STATUS: Contains {count} documents.")
            if count == 0:
                print("❌ CRITICAL WARNING: Database is empty! You must delete the folder and re-run.")
        except Exception as e:
            print(f"❌ DB CHECK FAILED: {e}")
    
    
    def _validate_db_compatibility(self):
        """
        Safety check: If you switch embedding models, you MUST clear the old DB
        because the vector dimensions (numbers) will be different.
        """
        if os.path.exists(self.persist_directory):
            print(f"⚠ WARNING: Using '{self.persist_directory}'. If this DB was created with Nomic/Ollama, it will CRASH with NVIDIA.")
            print("   -> Recommendation: Delete the './chroma_db' folder manually before running.")
    
    def _initialize_vector_store(self, json_path):
        print("Initializing vector store from JSON data...")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        for dataset in data:
            title = dataset.get('title', 'No Title')
            id = dataset.get('id', 'No ID')
            tags = dataset.get('tags', "No Tags")
            bands = dataset.get('bands', [])
            bands_info = "\n".join([f"- {band['name']}: {band['description']} (Unit: {band['unit']})" for band in bands])
            start_year = dataset.get('start_year', 'N/A')
            end_year = dataset.get('end_year', 'N/A')
            type = dataset.get('type', 'N/A')
            
            page_content = (
                f"Title: {title}\n"
                f"--------------------------------\n"
                f"DATASET NAME (Dataset ID)\n"
                f"Dataset ID: {id}\n"
                f"--------------------------------\n"
                f"Search Tags: {tags}\n"
                f"--------------------------------\n"
                f"AVAILABLE COLUMNS (Name : Description (Unit)):\n"
                f"{bands_info}\n"
                f"--------------------------------\n"
                f"Timeframe: from {start_year} to {end_year}\n"
                f"--------------------------------\n"
                f"Type: {type}\n"
                
            )
            
            metadata = {
                "title": title,
                "id": id,
                "tags": tags,
                "type": type
            }
            print(f"Adding document for dataset: {title} (ID: {id})")
            documents.append(Document(page_content=page_content, metadata=metadata))
            
            print(f"        ✔-> Document added for dataset: {title} (ID: {id})")
        
        # --- ROBUST BATCH PROCESSING ---
        print(f"🚀 Starting Batch Embedding for {len(documents)} documents...")
        
        vector_store = Chroma(
            embedding_function=self.embedding_model,
            persist_directory=self.persist_directory
        )
        
        # Start small to be safe
        BATCH_SIZE = 10 
        
        for i in range(0, len(documents), BATCH_SIZE):
            batch = documents[i : i + BATCH_SIZE]
            current_batch_num = (i // BATCH_SIZE) + 1
            total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE
            
            try:
                # Attempt to embed
                vector_store.add_documents(batch)
                print(f"   ✔ Batch {current_batch_num}/{total_batches} embedded.")
                
            except Exception as e:
                print(f"   ⚠️ Error on Batch {current_batch_num} (Size {len(batch)}): {e}")
                print("   🔄 Splitting batch into smaller chunks to retry...")
                
                # FALLBACK: If 10 fails, try doing them 1 by 1 (The "Nuclear" Option)
                time.sleep(2)
                for j, doc in enumerate(batch):
                    try:
                        vector_store.add_documents([doc])
                        print(f"      ✔ Saved Item {j+1}/{len(batch)} (Rescue Mode)")
                    except Exception as e2:
                        print(f"      ❌ SKIPPING CORRUPT ITEM {j+1}: {doc.metadata.get('id')}")
            
            # Tiny sleep to reset API limits
            time.sleep(0.5)

        print("✔ Vector DB Creation Complete.")
        return vector_store

    def _load_vector_store(self):
        if os.path.exists(self.persist_directory):
            print("Loading existing vector store from disk...")
            vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_model
            )
        else:
            return self._initialize_vector_store(self.json_path)
        
        return vector_store
    
    def generate_sql(self, user_query: str):
        system_prompt = """
        You are a Query Compiler for a Custom GEE Parser.
        
        ### 1. SYNTAX PROTOCOL (Strict)
        You must generate a single line of code adhering to this EXACT schema:
        SELECT <Band_ID> FROM {{gee:<Dataset_ID>|<Start_Date>|<End_Date>|<Lon>|<Lat>|<Scale>}}
        
        * **CRITICAL:** You MUST include the double curly braces {{gee:...}} around the table definition.
        * **CRITICAL:** Do NOT use wildcard (*). You MUST select the specific Band ID based on the description.

        ### 2. DATASET & BAND SELECTION (Context Strict)
        * **Dataset ID:** You must copy the ID EXACTLY from the provided "Context". Do not invent datasets (e.g., do not use JAXA unless it is in the context).
        * **Band ID:** Read the 'Description' of bands in the Context. Select the one matching the user's intent (e.g., "Greenness" -> 'NDVI').

        ### 3. PARAMETER EXTRACTION (NER)
        * **Start/End Date:** ISO 8601 (YYYY-MM-DD). Default: '2023-01-01' to '2023-12-31'.
        * **Lon/Lat:** Decimal coordinates.
          - If City/Country mentioned: Use internal knowledge to approximate coords.
          - Default: 0.0|0.0
        * **Scale:** Meters. Default: 1000.

        ### 4. OUTPUT
        * Return ONLY the SQL string.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Context Schema:\n{context}\n\nUser Request: {question}")
        ])

        def format_docs(docs):
            formatted_results = []
            for d in docs:
                content = (
                    f"=== CANDIDATE DATASET ===\n"
                    f"Dataset ID: {d.metadata.get('id')}\n"
                    f"{d.page_content}\n"
                    f"========================="
                )
                formatted_results.append(content)
            return "\n\n".join(formatted_results)

        rag_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

        print(f"DEBUG: Invoking RAG chain with query: {user_query}")
        try:
            result = rag_chain.invoke(user_query).strip()
            print(f"DEBUG: RAG chain result: {result}")
            return result
            
        except Exception as e:
            error_str = str(e)
            print(f"DEBUG: RAG chain failed: {error_str}")
            if "403" in error_str or "Forbidden" in error_str:
                print("\n❌ AUTHORIZATION ERROR: Your HF_TOKEN is invalid or does not have access to this model.")
                print("   1. Check if your token is correct in .env")
                print("   2. Ensure the token has 'Make calls to the serverless Inference API' permission.")
                print("   3. Try a smaller model by setting HF_MODEL in .env (e.g., HF_MODEL=meta-llama/Meta-Llama-3-8B-Instruct)")
            raise e