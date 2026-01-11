import pdfplumber
import os
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json
import tempfile

class ContractIngestor:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        
        # LangChain splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract raw text from a PDF file using pdfplumber.
        """
        full_text = ""
        try:
            print(f"{pdf_path}")
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"Found {total_pages} pages.")
                
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"

                    print(f"  - Extracted page {i+1}/{total_pages}")
        
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
        
        if full_text.strip() != "":
            return full_text
        
        else:
            from pdf2image import convert_from_path
            from paddleocr import PaddleOCR

            pocr = PaddleOCR(use_textline_orientation=True, lang='en')
            text = []
            pages = convert_from_path(pdf_path, dpi=300)

            with tempfile.TemporaryDirectory() as temp_dir:
                for i, page in enumerate(pages):
                    image_path = os.path.join(temp_dir, f"page_{i}.png")
                    page.save(image_path, "PNG")

                    result = pocr.predict(image_path)

                    if result and len(result) > 0:
                        text.extend(result[0].get("rec_texts", []))

                    print(f"  - OCR extracted page {i+1}/{len(pages)}")

            full_text = " ".join(text).strip()
            
            return full_text

    def clean_text(self, text: str) -> str:
        """
        Basic cleaning: remove excessive whitespace.
        """
        return text.strip()

    def chunk_text(self, text: str) -> List[Dict[str, str]]:
        """
        Split text using LangChain RecursiveCharacterTextSplitter.
        """
        raw_chunks = self.splitter.split_text(text)
        
        structured_chunks = []
        for i, content in enumerate(raw_chunks):
            if len(content) > 20:
                structured_chunks.append({
                    "id": f"chunk_{i}",
                    "text": content,
                    "metadata": {"source_type": "contract_pdf"} 
                })

        return structured_chunks

    def process_contract(self, pdf_path: str) -> List[Dict[str, str]]:
        print(f"Ingestion for: {pdf_path}")
        
        # Extract
        raw_text = self.extract_text_from_pdf(pdf_path)
        if not raw_text:
            print("No text extracted. Exiting.")
            return []

        # Chunk
        chunks = self.chunk_text(raw_text)
        
        print(f"Created {len(chunks)} chunks.")
        return chunks

if __name__ == "__main__":
    # target_pdf = "C:\\Users\\Sneha Shendre\\OneDrive\\Desktop\\legality-ai\\datasets\\contract.pdf"
    target_pdf = "C:\\Users\\Sneha Shendre\\OneDrive\\Desktop\\legality-ai\\pdf_to_final\\Screenshot 2025-12-26 234217.pdf"

    if os.path.exists(target_pdf):
        ingestor = ContractIngestor(chunk_size=400, chunk_overlap=100)
        chunks = ingestor.process_contract(target_pdf)
        
        output_file = "C:\\Users\\Sneha Shendre\\OneDrive\\Desktop\\legality-ai\\datasets\\pdf_chunks.json"
        
        print("\n--- PREVIEW OF OUTPUT ---")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n[ID: {chunk['id']}]")
            print(f"TEXT: {chunk['text']}...")
            print("-" * 40)
    else:
        print(f"\n[ERROR] File '{target_pdf}' not found.")


    if chunks:
        all_data = chunks
        with open(output_file, 'w') as f:
            json.dump(all_data, f, indent=4)
        print(f"\nSUCCESS! Generated {len(all_data)} items. Saved to {output_file}")