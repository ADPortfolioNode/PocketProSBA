"""
Gemini RAG Configuration for SBA Loan Information
This module configures the RAG system using Google Gemini API for SBA loan queries
"""

import os
import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.prompts import PromptTemplate

class GeminiRAGConfig:
    """Configuration class for Gemini-based SBA loan RAG system"""
    
    def __init__(self):
        self.collection_name = "sba_loans_gemini"
        self.persist_directory = "./pocketpro_vector_db"
        self.chunk_size = 1000
        self.chunk_overlap = 200
        
        # Gemini API configuration
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-pro"
        self.temperature = 0.7
        
    def get_prompt_template(self) -> PromptTemplate:
        """Get the prompt template for SBA loan queries"""
        
        template = """You are a knowledgeable SBA loan advisor powered by Google Gemini. Use the following context to answer questions about SBA loans accurately and helpfully.

Context: {context}

Question: {question}

Helpful Answer:"""
        
        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
    
    def get_text_splitter(self) -> RecursiveCharacterTextSplitter:
        """Get text splitter for SBA documents"""
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def get_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """Get Gemini embeddings for vector store"""
        return GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.gemini_api_key
        )
    
    def get_llm(self) -> ChatGoogleGenerativeAI:
        """Get Gemini language model for RAG"""
        return ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=self.temperature,
            google_api_key=self.gemini_api_key
        )

def create_sba_knowledge_base():
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
    
    # Create eligibility document
    with open("./backend/knowledge_base/sba_docs/sba_eligibility.txt", "w") as f:
        f.write("SBA LOAN ELIGIBILITY REQUIREMENTS - GEMINI RAG\n\n")
        f.write("BUSINESS SIZE: Must meet SBA size standards\n")
        f.write("BUSINESS TYPE: For-profit businesses, certain non-profits\n")
        f.write("LOCATION: US-based business\n")
        f.write("CREDIT REQUIREMENTS: Good personal credit, business credit history\n")
        f.write("COLLATERAL: May be required depending on loan amount\n")
    
    # Create application process document
    with open("./backend/knowledge_base/sba_docs/sba_application_process.txt", "w") as f:
        f.write("SBA LOAN APPLICATION PROCESS - GEMINI RAG\n\n")
        f.write("STEPS:\n")
        f.write("- Determine loan type and eligibility\n")
        f.write("- Prepare business plan and financial documents\n")
        f.write("- Find SBA-approved lender\n")
        f.write("- Complete loan application\n")
        f.write("- Provide required documentation\n")
        f.write("- Underwriting and approval process\n")
        f.write("- Loan closing and funding\n")
        f.write("\nTIMELINE: 30-90 days depending on loan type and complexity\n")
    
    # Create FAQ document
    with open("./backend/knowledge_base/sba_faq/sba_loan_faq.txt", "w") as f:
        f.write("SBA LOAN FREQUENTLY ASKED QUESTIONS - GEMINI RAG\n\n")
        f.write("Q: What is the maximum SBA loan amount?\n")
        f.write("A: SBA 7(a) loans can go up to $5 million, while 504 loans can go up to $5.5 million.\n\n")
        f.write("Q: How long does it take to get an SBA loan?\n")
        f.write("A: The typical timeline is 30-90 days depending on the loan type and complexity.\n\n")
        f.write("Q: What can SBA loans be used for?\n")
        f.write("A: Common uses include working capital, equipment purchases, real estate acquisition, and debt refinancing.\n\n")
        f.write("Q: Do I need collateral for an SBA loan?\n")
        f.write("A: Collateral may be required depending on the loan amount and type.\n\n")
        f.write("Q: What credit score is needed for an SBA loan?\n")
        f.write("A: Generally, a good personal credit score (680+) is recommended, along with strong business credit history.\n")

if __name__ == "__main__":
    create_sba_knowledge_base()
    print("SBA knowledge base created successfully for Gemini RAG!")
