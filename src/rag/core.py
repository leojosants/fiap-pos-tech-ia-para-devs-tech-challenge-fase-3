import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

def get_rag_engine(embeddings_model):
    """Inicializa e carrega o motor de busca vetorial (RAG) de forma robusta."""
    knowledge_content = {}
    
    try:
        # Caminho relativo à raiz do projeto
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        caminho_dados = os.path.join(base_dir, "knowledge")
        
        loader = DirectoryLoader(caminho_dados, glob="**/*.txt", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
        docs = loader.load()

        # Backup de texto puro para busca manual de segurança
        for doc in docs:
            filename = os.path.basename(doc.metadata['source'])
            knowledge_content[filename] = doc.page_content

        # Tenta criar o banco vetorial FAISS
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
        splits = text_splitter.split_documents(docs)
        vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings_model)
        
        return vectorstore.as_retriever(search_kwargs={"k": 1}), knowledge_content, True
        
    except Exception as e:
        print(f"⚠️ Erro no RAG Engine: {e}")
        return None, knowledge_content, False

def buscar_diretriz_manual(query, knowledge_content):
    """Busca alternativa de segurança via palavras-chave."""
    query = query.lower()
    if any(k in query for k in ["mama", "inca", "câncer", "papanicolau"]):
        return knowledge_content.get("protocolo_inca_mama.txt", "Consulte protocolos INCA.")
    if any(k in query for k in ["gravidez", "obstetricia", "pré-natal", "ferro"]):
        return knowledge_content.get("protocolo_febrasgo_obstetricia.txt", "Consulte diretrizes FEBRASGO.")
    if any(k in query for k in ["violencia", "segurança", "ajuda", "180"]):
        return knowledge_content.get("protocolo_violencia_domestica.txt", "Acione segurança e Ligue 180.")
    return "Consulte os protocolos oficiais na pasta /knowledge."
