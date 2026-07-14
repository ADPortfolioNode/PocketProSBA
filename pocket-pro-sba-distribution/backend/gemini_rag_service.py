"""
Gemini RAG Service for SBA Loan Information
This service provides RAG functionality using Google Gemini API for SBA loan queries
"""

import os
import logging
from typing import Dict, List, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.prompts import PromptTemplate

class GeminiRAGService:
    """Service class for Gemini-based SBA loan RAG functionality"""
    
    def __init__(self):
        self.collection_name = "sba_loans_gemini"
        self.persist_directory = "./pocketpro_vector_db"
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-pro"
        self.temperature = 0.7
        self.vector_store = None
        self.qa_chain = None
        self.logger = logging.getLogger(__name__)
        
    def initialize_vector_store(self) -> bool:
        """Initialize the Chroma vector store with SBA documents"""
        try:
            # Create knowledge base if it doesn't exist
            if not os.path.exists("./backend/knowledge_base"):
                self.create_sba_knowledge_base()
            
            # Initialize embeddings
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=self.gemini_api_key
            )
            
            # Initialize vector store
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=embeddings,
                persist_directory=self.persist_directory
            )
            
            # Load documents if vector store is empty
            if self.vector_store._collection.count() == 0:
                self._load_sba_documents()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {str(e)}")
            return False
    
    def create_sba_knowledge_base(self):
        """Create SBA knowledge base documents for Gemini RAG"""
        os.makedirs("./backend/knowledge_base/sba_docs", exist_ok=True)
        os.makedirs("./backend/knowledge_base/sba_faq", exist_ok=True)
        os.makedirs("./backend/knowledge_base/sba_guides", exist_ok=True)
        
        # Create SBA loan types document
        with open("./backend/knowledge_base/sba_docs/sba_loan_types.txt", "w") as f:
            f.write("SBA LOAN TYPES GUIDE - GEMINI RAG\n\n")
            f.write("SBA 7(A) LOANS:\n")
            f.write("Description: SBA 7(a) loans for general business purposes\n")
            f.write("Maximum Amount: $5 million\n")
            f.write("Use Cases: working capital, equipment, real estate, debt refinancing\n")
            f.write("Terms: up to 25 years for real estate, 10 years for equipment/working capital\n\n")
            
            f.write("SBA 504 LOANS:\n")
            f.write("Description: SBA 504 loans for major fixed assets\n")
            f.write("Maximum Amount: $5.5 million\n")
            f.write("Use Cases: real estate, major equipment, construction\n")
            f.write("Terms: 10, 20, or 25 years\n\n")
            
            f.write("SBA MICROLOANS:\n")
            f.write("Description: SBA Microloans for small businesses\n")
            f.write("Maximum Amount: $50,000\n")
            f.write("Use Cases: working capital, inventory, supplies, equipment\n")
            f.write("Terms: up to 6 years\n")
    
    def _load_sba_documents(self):
        """Load SBA documents into vector store"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Load documents from knowledge base
        loaders = [
            DirectoryLoader("./backend/knowledge_base/sba_docs", glob="**/*.txt", loader_cls=TextLoader),
            DirectoryLoader("./backend/knowledge_base/sba_faq", glob="**/*.txt", loader_cls=TextLoader),
            DirectoryLoader("./backend/knowledge_base/sba_guides", glob="**/*.txt", loader_cls=TextLoader)
        ]
        
        documents = []
        for loader in loaders:
            try:
                docs = loader.load()
                documents.extend(docs)
            except Exception as e:
                self.logger.warning(f"Could not load documents from {loader}: {str(e)}")
        
        # Split documents
        texts = text_splitter.split_documents(documents)
        
        # Add to vector store
        if texts:
            self.vector_store.add_documents(texts)
            self.vector_store.persist()
    
    def create_qa_chain(self) -> bool:
        """Create the QA chain for SBA loan queries"""
        try:
            if not self.vector_store:
                if not self.initialize_vector_store():
                    return False
            
            # Create retriever
            retriever = self.vector_store.as_retriever(
                search_kwargs={"k": 4}
            )
            
            # Create LLM
            llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=self.temperature,
                google_api_key=self.gemini_api_key
            )
            
            # Create prompt
            template = """You are a knowledgeable SBA loan advisor powered by Google Gemini. Use the following context to answer questions about SBA loans accurately and helpfully.

Context: {context}

Question: {question}

Helpful Answer:"""
            
            prompt = PromptTemplate(
                template=template,
                input_variables=["context", "question"]
            )
            
            # Create QA chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": prompt}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create QA chain: {str(e)}")
            return False
    
    def query_sba_loans(self, question: str) -> Dict[str, any]:
        """Query SBA loan information using Gemini RAG"""
        if not self.qa_chain:
            if not self.create_qa_chain():
                return {
                    "error": "RAG system not initialized",
                    "answer": "Sorry, I cannot process your question at this time."
                }
        
        try:
            # Process the query
            result = self.qa_chain({"query": question})
            
            # Format response
            response = {
                "question": question,
                "answer": result["result"],
                "source_documents": [
                    {
                        "content": doc.page_content[:200] + "...",
                        "metadata": doc.metadata
                    }
                    for doc in result.get("source_documents", [])
                ]
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return {
                "error": str(e),
                "answer": "Sorry, I encountered an error processing your question. Please try again."
            }
    
    def get_sba_overview(self) -> Dict[str, any]:
        """Get overview of available SBA loan information"""
        return {
            "available_loan_types": [
                "SBA 7(a) Loans",
                "SBA 504 Loans", 
                "SBA Microloans",
                "SBA Express Loans",
                "SBA Disaster Loans"
            ],
            "topics_covered": [
                "Loan eligibility requirements",
                "Application process steps",
                "Required documentation",
                "Interest rates and terms",
                "Collateral requirements",
                "Timeline expectations"
            ],
            "sample_questions": [
                "What are the eligibility requirements for an SBA 7(a) loan?",
                "How long does the SBA loan application process take?",
                "What documents do I need to apply for an SBA loan?",
                "What can SBA loans be used for?",
                "What are the current SBA loan interest rates?"
            ]
        }

# Global RAG service instance
gemini_rag_service = GeminiRAGService()
