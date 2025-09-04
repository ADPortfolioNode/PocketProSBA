"""
Enhanced Gemini RAG Service for SBA Loan Information
Full production-ready RAG functionality using Google Gemini API
"""

import os
import logging
import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.prompts import PromptTemplate
from langchain.schema import Document
import chromadb

class EnhancedGeminiRAGService:
    """Enhanced service class for full Gemini-based SBA loan RAG functionality"""
    
    def __init__(self):
        self.collection_name = "sba_loans_gemini_production"
        self.persist_directory = "./pocketpro_vector_db"
        self.chunk_size = 1500
        self.chunk_overlap = 300
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-pro"
        self.temperature = 0.3
        self.vector_store = None
        self.qa_chain = None
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.is_initialized = False
        
    def initialize_full_service(self) -> bool:
        """Initialize the complete RAG service with all components"""
        try:
            self.logger.info("🚀 Initializing Enhanced Gemini RAG Service...")
            
            # Check API key
            if not self.gemini_api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required")
            
            # Create comprehensive knowledge base
            self._create_comprehensive_knowledge_base()
            
            # Initialize vector store
            if not self._initialize_vector_store():
                return False
            
            # Create QA chain
            if not self._create_enhanced_qa_chain():
                return False
            
            self.is_initialized = True
            self.logger.info("✅ Enhanced Gemini RAG Service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG service: {str(e)}")
            return False
    
    def _create_comprehensive_knowledge_base(self):
        """Create comprehensive SBA knowledge base with detailed documents"""
        base_path = "./backend/knowledge_base"
        
        # Create directory structure
        directories = [
            f"{base_path}/sba_docs",
            f"{base_path}/sba_faq",
            f"{base_path}/sba_guides",
            f"{base_path}/sba_programs",
            f"{base_path}/sba_requirements",
            f"{base_path}/sba_calculator"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        # Create comprehensive SBA loan documents
        self._create_sba_loan_types_doc()
        self._create_sba_eligibility_doc()
        self._create_sba_application_doc()
        self._create_sba_rates_terms_doc()
        self._create_sba_faq_doc()
        self._create_sba_programs_doc()
        self._create_sba_calculator_doc()
    
    def _create_sba_loan_types_doc(self):
        """Create detailed SBA loan types documentation"""
        content = """SBA LOAN TYPES - COMPREHENSIVE GUIDE

SBA 7(A) LOANS - GENERAL BUSINESS FINANCING:
Maximum Amount: $5 million
Interest Rates: Prime + 2.25% to 4.75% (variable)
Terms: Up to 25 years for real estate, 10 years for equipment, 7 years for working capital
Use Cases: Working capital, equipment purchases, real estate acquisition, debt refinancing, business acquisition
Down Payment: As low as 10%
Processing Time: 5-10 business days for Express, 30-90 days for standard

SBA 504 LOANS - MAJOR FIXED ASSETS:
Maximum Amount: $5.5 million per project ($16.5 million aggregate)
Interest Rates: Fixed rates, typically below market
Terms: 10, 20, or 25 years
Use Cases: Real estate purchase, construction, major equipment
Structure: 50% bank loan, 40% SBA debenture, 10% borrower equity
Benefits: Below-market fixed rates, long-term financing

SBA MICROLOANS - SMALL BUSINESS FUNDING:
Maximum Amount: $50,000
Average Loan: $13,000
Interest Rates: 8-13% (varies by intermediary)
Terms: Up to 6 years
Use Cases: Working capital, inventory, supplies, equipment, furniture
Providers: Nonprofit intermediary lenders
Target: Startups and small businesses
"""
        
        with open("./backend/knowledge_base/sba_docs/sba_loan_types_comprehensive.txt", "w") as f:
            f.write(content)
    
    def _create_sba_eligibility_doc(self):
        """Create detailed eligibility requirements documentation"""
        content = """SBA LOAN ELIGIBILITY REQUIREMENTS - DETAILED GUIDE

BUSINESS SIZE REQUIREMENTS:
- Manufacturing: 500-1,500 employees (varies by NAICS code)
- Wholesale: 100-500 employees
- Retail/Service: $7.5M-$38.5M annual receipts (varies by industry)
- Construction: $36.5M-$39.5M average annual receipts
- Agriculture: $1M-$2.5M average annual receipts

BUSINESS TYPE ELIGIBILITY:
✅ ELIGIBLE:
- For-profit businesses
- Certain nonprofits (504 program)
- Cooperatives
- Employee Stock Ownership Plans (ESOPs)

❌ INELIGIBLE:
- Nonprofits (except 504 program)
- Religious organizations
- Gambling businesses
- Cannabis businesses
- Passive businesses (real estate investment)
- Speculative businesses
- Pyramid sales plans

CREDIT REQUIREMENTS:
- Personal Credit Score: 680+ recommended (some lenders accept 650+)
- Business Credit Score: Establish business credit history
- Debt Service Coverage Ratio: 1.15x minimum
- Time in Business: 2+ years preferred (startups considered with strong plan)
- No recent bankruptcies or defaults on federal debt

COLLATERAL REQUIREMENTS:
- Personal guarantee required for owners with 20%+ ownership
- Business assets as primary collateral
- Personal assets may be required
- Real estate collateral for larger loans
- No collateral required for loans under $25,000

DOCUMENTATION REQUIREMENTS:
- Business plan with 3-5 year projections
- Personal and business tax returns (3 years)
- Personal financial statement (SBA Form 413)
- Business financial statements (YTD balance sheet, P&L)
- Debt schedule
- Business licenses and registrations
- Articles of incorporation/organization
- Operating agreements/bylaws
- Resumes for key management
"""
        
        with open("./backend/knowledge_base/sba_requirements/sba_eligibility_detailed.txt", "w") as f:
            f.write(content)
    
    def _create_sba_application_doc(self):
        """Create detailed application process documentation"""
        content = """SBA LOAN APPLICATION PROCESS - STEP BY STEP

PHASE 1: PREPARATION (1-2 weeks)
1. Determine loan type and amount needed
2. Check eligibility requirements
3. Gather preliminary documentation
4. Research SBA-approved lenders
5. Prepare business plan and financial projections

PHASE 2: LENDER SELECTION (1 week)
1. Compare 3-5 SBA-approved lenders
2. Evaluate rates, terms, and requirements
3. Check lender's SBA loan volume and experience
4. Understand lender's specific requirements
5. Get pre-qualification if available

PHASE 3: APPLICATION SUBMISSION (1-2 weeks)
1. Complete SBA loan application (SBA Form 1919)
2. Submit business plan and financial projections
3. Provide all required documentation
4. Pay application fee (varies by lender)
5. Submit to chosen SBA-approved lender

PHASE 4: UNDERWRITING (2-4 weeks)
1. Lender reviews application and documentation
2. Credit analysis and risk assessment
3. Collateral evaluation
4. SBA guarantee processing (if required)
5. Conditional approval or denial

PHASE 5: CLOSING (1-2 weeks)
1. Final approval from lender and SBA
2. Loan documentation preparation
3. Legal review and signing
4. Funding and disbursement

TIMELINE SUMMARY:
- Express Loans: 30-36 hours approval, 30 days total
- Standard 7(a): 30-90 days total
- 504 Loans: 45-120 days total
- Microloans: 30-60 days total

ACCELERATION TIPS:
- Work with experienced SBA lender
- Prepare complete documentation upfront
- Respond quickly to lender requests
- Consider SBA Express for faster processing
- Use SBA Preferred Lenders Program (PLP)
"""
        
        with open("./backend/knowledge_base/sba_guides/sba_application_process_detailed.txt", "w") as f:
            f.write(content)
    
    def _create_sba_rates_terms_doc(self):
        """Create current rates and terms documentation"""
        content = """SBA LOAN RATES AND TERMS - CURRENT INFORMATION

CURRENT SBA 7(A) RATES (2024):
- Prime Rate: 8.50% (as of December 2024)
- Variable Rate Loans: Prime + 2.25% to 4.75% = 10.75% to 13.25%
- Fixed Rate Loans: 13.50% to 16.50% (varies by lender)
- SBA Guaranty Fee: 0% to 3.75% (based on loan amount and maturity)

CURRENT SBA 504 RATES (2024):
- 25-year debenture: 5.81% (December 2024)
- 20-year debenture: 5.74% (December 2024)
- 10-year debenture: 5.69% (December 2024)
- Effective rate to borrower: Typically 1-2% below conventional financing

SBA MICROLOAN RATES:
- Typical Range: 8% to 13%
- Varies by intermediary lender
- No SBA guaranty fees

FEE STRUCTURE:
- SBA Guaranty Fee: 0% for loans under $500,000, 0.55% to 3.75% for larger loans
- Lender Fees: 0% to 2% (varies by lender)
- Third-party fees: Appraisal, environmental, legal (typically $2,000-$5,000)
- Packaging fees: 0% to 3% (if using loan packager)

TERMS BY LOAN TYPE:
- Working Capital: Up to 7 years
- Equipment: Up to 10 years (or useful life)
- Real Estate: Up to 25 years
- Business Acquisition: Up to 10 years
- Debt Refinancing: Up to 7 years (original debt term)

PREPAYMENT PENALTIES:
- 7(a) Loans: 5-3-1 structure (5% year 1, 3% year 2, 1% year 3, none after)
- 504 Loans: 10-year declining prepayment penalty
- Microloans: Varies by intermediary
"""
        
        with open("./backend/knowledge_base/sba_docs/sba_rates_terms_current.txt", "w") as f:
            f.write(content)
    
    def _create_sba_faq_doc(self):
        """Create comprehensive FAQ"""
        content = """SBA LOAN FREQUENTLY ASKED QUESTIONS - COMPREHENSIVE

Q: What is the maximum SBA loan amount?
A: SBA 7(a) loans can go up to $5 million, 504 loans up to $5.5 million per project, and microloans up to $50,000.

Q: How long does it take to get an SBA loan?
A: Express loans: 30-36 hours approval, 30 days total. Standard 7(a): 30-90 days. 504 loans: 45-120 days. Microloans: 30-60 days.

Q: What credit score is needed for an SBA loan?
A: 680+ recommended for best rates, some lenders accept 650+. Strong business credit history also required.

Q: Can I get an SBA loan to start a business?
A: Yes, but you'll need a strong business plan, industry experience, and good personal credit. Consider SBA microloans for smaller amounts.

Q: What can SBA loans be used for?
A: Working capital, equipment purchases, real estate acquisition, business acquisition, debt refinancing, construction, inventory.

Q: Do I need collateral for an SBA loan?
A: Collateral may be required for loans over $25,000. Personal guarantee required for owners with 20%+ ownership.

Q: Are SBA loans personally guaranteed?
A: Yes, personal guarantees are required for all owners with 20% or more ownership.

Q: Can I get an SBA loan with bad credit?
A: Generally no, but some lenders may consider with strong compensating factors like significant collateral or high revenue.

Q: What is the SBA guaranty fee?
A: 0% for loans under $500,000, 0.55% to 3.75% for larger loans, based on loan amount and maturity.

Q: Can I pay off an SBA loan early?
A: Yes, but prepayment penalties may apply for 7(a) loans (5-3-1 structure) and 504 loans (10-year declining).

Q: How much down payment is required?
A: As low as 10% for 7(a) loans, 10% for 504 loans, varies by lender and loan type.

Q: Can I use an SBA loan to buy a business?
A: Yes, SBA loans can be used for franchise purchases if the franchise is SBA-approved.
"""
        
        with open("./backend/knowledge_base/sba_faq/sba_comprehensive_faq.txt", "w") as f:
            f.write(content)
    
    def _create_sba_programs_doc(self):
        """Create SBA program documentation"""
        content = """SBA PROGRAMS AND SERVICES - COMPLETE GUIDE

SBA 7(A) PROGRAM VARIATIONS:
- Standard 7(a): Up to $5M, full underwriting
- SBA Express: Up to $500K, 36-hour approval
- Export Express: Up to $500K for exporters
- Export Working Capital: Up to $5M for export financing
- International Trade: Up to $5M for trade competition
- CAPLines: Working capital lines of credit
- Veterans Advantage: Reduced fees for veterans

SBA 504 PROGRAM DETAILS:
- CDC/504: Real estate and equipment financing
- Green 504: Energy-efficient projects
- Refinancing 504: Refinance existing debt
- 504 First Mortgage: Bank portion up to 50%
- 504 Debenture: SBA portion up to 40%

SBA MICROLOAN PROGRAM:
- CDC/504: Real estate and equipment financing
- Maximum: $50,000
- Average: $13,000
- Intermediaries: Nonprofit lenders
- Technical assistance included
- Startup-friendly

SBA DISASTER LOANS:
- Physical Damage: Repair/replace damaged property
- Economic Injury: Working capital during disaster recovery
- Military Reservist: Economic injury from military call-up
- Home and Personal: For homeowners and renters

SBA SURETY BONDS:
- Bid bonds: Guarantee project bidding
- Performance bonds: Guarantee project completion
- Payment bonds: Guarantee payment to subcontractors
- Ancillary bonds: Other contract requirements

SBA EXPORT PROGRAMS:
- Export Express: Streamlined export financing
- Export Working Capital: Short-term export financing
- International Trade: Long-term trade financing
- STEP grants: State trade expansion program

SBA GRANTS AND COMPETITIONS:
- SBIR/STTR: Small business innovation research
- Growth Accelerator Fund: Startup accelerators
- Veterans Business Outreach Centers: Training and counseling
- Women's Business Centers: Training and resources
- SCORE: Free mentoring and education
"""
        
        with open("./backend/knowledge_base/sba_programs/sba_programs_complete.txt", "w") as f:
            f.write(content)
    
    def _create_sba_calculator_doc(self):
        """Create loan calculator documentation"""
        content = """SBA LOAN CALCULATOR GUIDE - HOW TO ESTIMATE PAYMENTS

LOAN PAYMENT CALCULATION FACTORS:
- Loan Amount: Principal borrowed
- Interest Rate: Annual percentage rate
- Loan Term: Years to repay
- Payment Frequency: Monthly standard

SAMPLE CALCULATIONS:

$100,000 LOAN EXAMPLES:
- 7% interest, 10 years = $1,161/month
- 8% interest, 7 years = $1,559/month
- 9% interest, 5 years = $2,076/month

$500,000 LOAN EXAMPLES:
- 7% interest, 25 years = $3,534/month
- 8% interest, 20 years = $4,182/month
- 9% interest, 15 years = $5,071/month

$1,000,000 LOAN EXAMPLES:
- 7% interest, 25 years = $7,068/month
- 8% interest, 20 years = $8,364/month
- 9% interest, 15 years = $10,142/month

DEBT SERVICE COVERAGE RATIO:
- Formula: Net Operating Income / Annual Debt Service
- SBA Requirement: 1.15x minimum
- Example: $150,000 NOI / $130,435 debt service = 1.15x

LOAN-TO-VALUE RATIOS:
- Real Estate: Up to 90% LTV
- Equipment: Up to 80% LTV
- Business Acquisition: Up to 80% LTV
- Working Capital: No specific LTV

DOWN PAYMENT CALCULATOR:
- 7(a) Loans: 10% minimum
- 504 Loans: 10% borrower contribution
- Example: $500,000 purchase = $50,000 down payment

WORKING CAPITAL CALCULATION:
- Formula: Current Assets - Current Liabilities
- SBA considers working capital needs in loan sizing
- Include 3-6 months operating expenses

EQUIPMENT FINANCING:
- Use equipment as collateral
- Terms match equipment life (3-10 years)
- Include soft costs (installation, training)

REAL ESTATE FINANCING:
- 25-year maximum term
- Property must be 51% owner-occupied
- Appraisal required for loans over $250,000
"""
        
        with open("./backend/knowledge_base/sba_calculator/sba_loan_calculator_guide.txt", "w") as f:
            f.write(content)
    
    def _initialize_vector_store(self) -> bool:
        """Initialize the Chroma vector store with comprehensive documents"""
        try:
            # Initialize embeddings
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=self.gemini_api_key
            )
            
            # Initialize Chroma client
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Get or create collection
            try:
                collection = self.client.get_collection(name=self.collection_name)
            except Exception:
                collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            
            # Initialize vector store
            self.vector_store = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=embeddings,
                persist_directory=self.persist_directory
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {str(e)}")
            return False
    
    def _create_enhanced_qa_chain(self) -> bool:
        """Create enhanced QA chain with better prompts and configuration"""
        try:
            if not self.vector_store:
                return False
            
            # Create retriever
            retriever = self.vector_store.as_retriever(
                search_kwargs={"k": 6}
            )
            
            # Create LLM
            llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=self.temperature,
                google_api_key=self.gemini_api_key
            )
            
            # Create enhanced prompt
            template = """You are PocketPro SBA, an expert SBA loan advisor. Use the context to answer accurately.

Context: {context}

Question: {question}

Answer:"""
            
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
    
    def query_sba_loans(self, question: str) -> Dict[str, Any]:
        """Query SBA loan information using enhanced Gemini RAG"""
        if not self.qa_chain:
            return {"error": "Service not ready"}
        
        try:
            result = self.qa_chain({"query": question})
            return {
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
        except Exception as e:
            return {"error": str(e)}
    
    def search_documents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search documents using semantic similarity"""
        if not self.vector_store:
            return []
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=limit)
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    "metadata": doc.metadata,
                    "relevance_score": float(score),
                    "id": hashlib.md5(doc.page_content.encode()).hexdigest()[:8]
                })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def get_sba_overview(self) -> Dict[str, Any]:
        """Get comprehensive overview of available SBA information"""
        return {
            "available_loan_types": [
                {
                    "type": "SBA 7(a) Loans",
                    "max_amount": "$5 million",
                    "use_cases": ["working capital", "equipment", "real estate", "business acquisition"],
                    "terms": "7-25 years",
                    "rates": "Prime + 2.25% to 4.75%"
                },
                {
                    "type": "SBA 504 Loans",
                    "max_amount": "$5.5 million per project",
                    "use_cases": ["real estate", "major equipment", "construction"],
                    "terms": "10-25 years",
                    "rates": "Fixed, below market"
                },
                {
                    "type": "SBA Microloans",
                    "max_amount": "$50,000",
                    "use_cases": ["working capital", "inventory", "supplies", "equipment"],
                    "terms": "Up to 6 years",
                    "rates": "8-13% (varies by lender)"
                },
                {
                    "type": "SBA Express Loans",
                    "max_amount": "$500,000",
                    "use_cases": ["same as 7(a) but faster"],
                    "terms": "7-25 years",
                    "rates": "Prime + 4.5% to 6.5%"
                }
            ],
            "topics_covered": [
                "Loan eligibility requirements",
                "Application process steps",
                "Required documentation",
                "Current interest rates and terms",
                "Collateral requirements",
                "Timeline expectations",
                "Fee structures",
                "Prepayment penalties",
                "Down payment requirements"
            ],
            "sample_questions": [
                "What are the eligibility requirements for an SBA 7(a) loan?",
                "How long does the SBA loan application process take?",
                "What documents do I need to apply for an SBA loan?",
                "What can SBA loans be used for?",
                "What are the current SBA loan interest rates?",
                "How much down payment is required?",
                "What is the maximum SBA loan amount?",
                "Can I use an SBA loan to buy a business?",
                "What credit score is needed for an SBA loan?",
                "Are SBA loans personally guaranteed?"
            ],
            "calculator_tools": [
                "Loan payment estimator",
                "Debt service coverage calculator",
                "Down payment calculator",
                "Working capital needs assessment"
            ]
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        try:
            doc_count = 0
            if self.client and self.collection_name:
                try:
                    collection = self.client.get_collection(name=self.collection_name)
                    doc_count = collection.count()
                except:
                    doc_count = 0

            return {
                "service_name": "Enhanced Gemini RAG Service",
                "is_initialized": self.is_initialized,
                "document_count": doc_count,
                "collection_name": self.collection_name,
                "model_name": self.model_name,
                "temperature": self.temperature
            }

        except Exception as e:
            return {
                "error": str(e),
                "is_initialized": False,
                "document_count": 0
            }

# Global enhanced RAG service instance
enhanced_rag_service = EnhancedGeminiRAGService()
