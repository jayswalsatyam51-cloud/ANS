#Imports and Setup
import streamlit as st
from PyPDF2 import PdfReader
import PyPDF2
import fitz  # PyMuPDF - much better for text extraction
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import time
import re

# OCR libs (optional fallback)
try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    st.warning("⚠️ OCR libraries not available. Install pdf2image and pytesseract for scanned PDF support.")

# Load API key
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    st.error("❌ GROQ_API_KEY not found in environment variables!")

# Token counting helper function
def count_tokens_approx(text):
    """Rough approximation of token count (1 token ≈ 4 characters)"""
    return len(text) // 4

# IMPROVED PDF text extraction with multiple methods
def get_pdf_text(pdf_docs):
    text = ""
    total_pages = 0
    extraction_stats = {"successful_pages": 0, "ocr_pages": 0, "failed_pages": 0}
    
    for pdf_idx, pdf in enumerate(pdf_docs):
        try:
            # Method 1: Try PyMuPDF first (better text extraction)
            pdf_document = fitz.open(stream=pdf.read(), filetype="pdf")
            pdf_pages = len(pdf_document)
            total_pages += pdf_pages
            
            st.info(f"📖 Processing PDF {pdf_idx + 1}: {pdf_pages} pages")
            
            # Reset file pointer for PyPDF2 fallback
            pdf.seek(0)
            
            for page_num in range(pdf_pages):
                try:
                    # Try PyMuPDF first
                    page = pdf_document[page_num]
                    page_text = page.get_text()
                    
                    if page_text and len(page_text.strip()) > 50:  # Good text extraction
                        text += f"\n=== Page {page_num + 1} of PDF {pdf_idx + 1} ===\n"
                        # Clean up text
                        page_text = re.sub(r'\s+', ' ', page_text)  # Normalize whitespace
                        page_text = re.sub(r'\n+', '\n', page_text)  # Remove excessive newlines
                        text += page_text.strip()
                        text += "\n\n"
                        extraction_stats["successful_pages"] += 1
                    else:
                        # Fallback to PyPDF2
                        pdf_reader = PdfReader(pdf)
                        if page_num < len(pdf_reader.pages):
                            fallback_text = pdf_reader.pages[page_num].extract_text()
                            if fallback_text and len(fallback_text.strip()) > 50:
                                text += f"\n=== Page {page_num + 1} of PDF {pdf_idx + 1} ===\n"
                                text += fallback_text.strip()
                                text += "\n\n"
                                extraction_stats["successful_pages"] += 1
                            else:
                                # Last resort: OCR
                                if OCR_AVAILABLE:
                                    st.warning(f"⚠️ Using OCR for page {page_num + 1} - this may take longer")
                                    try:
                                        pdf.seek(0)
                                        images = convert_from_path(pdf, first_page=page_num+1, last_page=page_num+1)
                                        for img in images:
                                            ocr_text = pytesseract.image_to_string(img, config='--psm 6')
                                            if ocr_text.strip():
                                                text += f"\n=== Page {page_num + 1} of PDF {pdf_idx + 1} (OCR) ===\n"
                                                text += ocr_text.strip()
                                                text += "\n\n"
                                                extraction_stats["ocr_pages"] += 1
                                                break
                                    except Exception as ocr_error:
                                        st.warning(f"OCR failed for page {page_num + 1}: {str(ocr_error)}")
                                        extraction_stats["failed_pages"] += 1
                                else:
                                    extraction_stats["failed_pages"] += 1
                        
                except Exception as page_error:
                    st.warning(f"Error processing page {page_num + 1}: {str(page_error)}")
                    extraction_stats["failed_pages"] += 1
                    continue
            
            pdf_document.close()
            
        except Exception as pdf_error:
            st.error(f"Error processing PDF {pdf_idx + 1}: {str(pdf_error)}")
            continue
    
    # Show extraction statistics
    total_chars = len(text)
    st.success(f"✅ Extracted {total_chars:,} characters from {total_pages} pages")
    st.info(f"📊 Success: {extraction_stats['successful_pages']} | OCR: {extraction_stats['ocr_pages']} | Failed: {extraction_stats['failed_pages']}")
    
    # Debug: Show sample of extracted text
    if text:
        preview = text[:500] + "..." if len(text) > 500 else text
        st.text_area("📄 Text Preview (first 500 chars):", preview, height=100)
    
    return text

# IMPROVED text chunking with better overlap strategy
def get_text_chunks(text):
    if not text or len(text.strip()) < 100:
        st.error("❌ Insufficient text extracted for processing")
        return []
    
    # Use optimized chunking for better context preservation
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,      # Larger chunks for better context
        chunk_overlap=400,    # More overlap to preserve context
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]  # Better separators
    )
    
    chunks = text_splitter.split_text(text)
    
    # Filter out very short chunks
    chunks = [chunk for chunk in chunks if len(chunk.strip()) > 100]
    
    # Show chunk statistics
    st.info(f"📝 Created {len(chunks)} text chunks (avg {len(text)//len(chunks) if chunks else 0} chars per chunk)")
    
    return chunks

# Store embeddings in FAISS with better error handling
def get_vector_store(text_chunks, embedding_model="sentence-transformers/all-MiniLM-L6-v2"):
    if not text_chunks:
        raise ValueError("No text chunks were created. Check if your PDF has extractable text.")

    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        st.info(f"🔄 Creating vector embeddings for {len(text_chunks)} chunks...")
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
        vector_store.save_local("faiss_index")
        st.success("✅ Vector store created successfully!")
        
    except Exception as e:
        st.error(f"❌ Error loading embedding model '{embedding_model}': {str(e)}")
        st.info("🔄 Falling back to general purpose model...")
        
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
        vector_store.save_local("faiss_index")
        st.session_state.embedding_model = "sentence-transformers/all-MiniLM-L6-v2"

# IMPROVED QA chain with better prompting
def get_conversational_chain(model_name="llama-3.3-70b-versatile"):
    prompt_template = """
    You are an expert document analyst. Answer the question based on the provided context with maximum detail and accuracy.

    Instructions:
    1. Use ALL relevant information from the context
    2. Provide a comprehensive answer with specific details
    3. Include relevant quotes or examples when appropriate
    4. If information spans multiple sections, synthesize it coherently
    5. Only say "Answer is not available in the context" if truly no relevant information exists
    6. Structure your response with clear headings if the answer has multiple parts

    Context:
    {context}

    Question: {question}

    Detailed Answer:
    """

    model = ChatGroq(
        groq_api_key=groq_api_key,
        model_name=model_name,
        temperature=0.1,  # Lower temperature for more focused answers
        max_tokens=4000   # Allow longer responses
    )

    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

# ENHANCED retrieval with better context management
def limit_context_size(docs, max_tokens=6000):  # Increased limit
    """Limit the total context size while prioritizing most relevant content"""
    limited_docs = []
    total_tokens = 0
    
    for i, doc in enumerate(docs):
        doc_tokens = count_tokens_approx(doc.page_content)
        
        if total_tokens + doc_tokens > max_tokens:
            remaining_tokens = max_tokens - total_tokens
            remaining_chars = remaining_tokens * 4
            
            if remaining_chars > 200:  # Include more partial content
                truncated_content = doc.page_content[:remaining_chars]
                # Try to end at a sentence or paragraph boundary
                for boundary in ['\n\n', '. ', '\n', ';']:
                    last_boundary = truncated_content.rfind(boundary)
                    if last_boundary > remaining_chars * 0.6:
                        truncated_content = truncated_content[:last_boundary + len(boundary)]
                        break
                
                doc.page_content = truncated_content + "..."
                limited_docs.append(doc)
            break
            
        limited_docs.append(doc)
        total_tokens += doc_tokens
    
    return limited_docs

# ENHANCED user input with better retrieval
def user_input(user_question, embedding_model="sentence-transformers/all-MiniLM-L6-v2", llm_model="llama3-8b-8192"):
    try:
        # Load embeddings
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        except Exception as e:
            st.warning(f"⚠️ Error loading embedding model. Using fallback.")
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        
        st.info("🔍 Searching through document...")
        
        # Enhanced retrieval strategy
        docs_similarity = new_db.similarity_search(user_question, k=15)  # Get more docs
        
        # Try MMR search for diversity
        try:
            docs_mmr = new_db.max_marginal_relevance_search(user_question, k=10, fetch_k=25)
            # Combine and deduplicate
            all_docs = docs_similarity + [doc for doc in docs_mmr if doc not in docs_similarity]
        except:
            all_docs = docs_similarity
        
        st.info(f"🔄 Found {len(all_docs)} relevant document sections")
        
        if all_docs:
            preview_text = all_docs[0].page_content[:300] + "..." if len(all_docs[0].page_content) > 300 else all_docs[0].page_content
            st.success(f"🎯 Most relevant section preview:\n{preview_text}")
        
        # Limit context size
        limited_docs = limit_context_size(all_docs, max_tokens=6000)
        
        if not limited_docs:
            st.warning("No relevant context found for your question.")
            return
        
        # Show context info
        total_context_tokens = sum(count_tokens_approx(doc.page_content) for doc in limited_docs)
        st.info(f"📊 Using {len(limited_docs)} document sections ({total_context_tokens} estimated tokens)")
        
        chain = get_conversational_chain(llm_model)

        # Execute with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with st.spinner("🤔 Analyzing content and generating comprehensive answer..."):
                    response = chain(
                        {"input_documents": limited_docs, "question": user_question},
                        return_only_outputs=True
                    )
                
                # Display response
                st.markdown("### 📝 Answer:")
                st.write(response["output_text"])
                
                # Show sources
                st.markdown("### 📚 Sources:")
                st.info(f"Answer based on {len(limited_docs)} document sections from your uploaded PDF(s)")
                
                # Debug: Show used context (optional)
                with st.expander("🔍 View Retrieved Context (Debug)"):
                    for i, doc in enumerate(limited_docs[:3]):  # Show first 3 docs
                        st.text_area(f"Context {i+1}:", doc.page_content[:500], height=100)
                
                break
                
            except Exception as e:
                error_msg = str(e)
                if "rate_limit_exceeded" in error_msg or "413" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        st.warning(f"Rate limit hit. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        
                        if len(limited_docs) > 2:
                            limited_docs = limited_docs[:len(limited_docs)//2]
                    else:
                        st.error(f"⚠️ Rate limit exceeded after {max_retries} attempts.")
                else:
                    st.error(f"⚠️ Error: {error_msg}")
                    break
                    
    except FileNotFoundError:
        st.error("❌ Please upload and process PDF files first using the sidebar.")
    except Exception as e:
        st.error(f"⚠️ Error while answering: {e}")

# Streamlit UI
def main():
    st.set_page_config("Enhanced PDF Chat", page_icon="📚", layout="wide")
    st.header("📚 Enhanced Multi-PDF Chat AI Agent")
    
    st.info("💡 This enhanced app uses better text extraction and retrieval. Upload your PDFs and ask detailed questions!")

    user_question = st.text_input("Ask a Question from the PDF Files", 
                                 placeholder="e.g., What are the main findings? Summarize the key points.")

    if user_question:
        embedding_model = st.session_state.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
        llm_model = st.session_state.get('llm_model', 'llama-3.3-70b-versatile')
        user_input(user_question, embedding_model, llm_model)

    with st.sidebar:
        st.title("⚙️ Configuration:")
        
        # Embedding models
        embedding_models = {
            "All-MiniLM-L6-v2 (General)": "sentence-transformers/all-MiniLM-L6-v2",
            "All-mpnet-base-v2 (Better)": "sentence-transformers/all-mpnet-base-v2",
        }
        
        selected_embedding = st.selectbox(
            "Choose Embedding Model:",
            list(embedding_models.keys()),
            index=1
        )
        
        embedding_model_name = embedding_models[selected_embedding]
        
        # LLM models
        llm_models = {
            "Llama3-8B (Fast)": "llama3-8b-8192",
            "Llama3.3-70B (Best)": "llama-3.3-70b-versatile",
            "Mixtral-8x7B": "mixtral-8x7b-32768"
        }
        
        selected_llm = st.selectbox(
            "Choose LLM Model:",
            list(llm_models.keys()),
            index=1
        )
        
        llm_model_name = llm_models[selected_llm]
        
        st.markdown("---")
        st.markdown("📄 **Upload Documents:**")
        
        pdf_docs = st.file_uploader(
            "Upload your PDF Files", 
            accept_multiple_files=True,
            type=["pdf"]
        )
        
        if st.button("🚀 Submit & Process", use_container_width=True):
            if not pdf_docs:
                st.error("❌ Please upload at least one PDF file.")
                return
                    
            with st.spinner("Processing your documents..."):
                try:
                    raw_text = get_pdf_text(pdf_docs)

                    if not raw_text.strip():
                        st.error("❌ No text could be extracted. PDF may be scanned, encrypted, or empty.")
                        return

                    text_chunks = get_text_chunks(raw_text)
                    
                    if not text_chunks:
                        st.error("❌ Could not create text chunks. Please check your PDF.")
                        return
                    
                    st.session_state.embedding_model = embedding_model_name
                    st.session_state.llm_model = llm_model_name
                    
                    get_vector_store(text_chunks, embedding_model_name)
                    st.success("✅ PDF processed successfully!")
                    
                    # Processing summary
                    st.markdown("### 📊 Processing Summary:")
                    st.write(f"- **Text extracted:** {len(raw_text):,} characters")
                    st.write(f"- **Chunks created:** {len(text_chunks)}")
                    st.write(f"- **Models:** {selected_embedding} + {selected_llm}")
                    
                except Exception as e:
                    st.error(f"⚠️ Error while processing: {e}")
                    st.info("💡 Try a different PDF or check if the file is corrupted.")

if __name__ == "__main__":
    main()