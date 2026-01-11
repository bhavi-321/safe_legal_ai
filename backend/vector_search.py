import json
# import numpy as np
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from ingestion_pipeline import ContractIngestor

class RiskDetector:
    def __init__(self, gold_standard_path):
        if os.path.exists('./legal_risk_model'):
            self.model = SentenceTransformer('./legal_risk_model')
        else:
            print("Custom model not found. Using generic 'all-MiniLM-L6-v2'...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')

        self.gold_standard = self.load_gold_standard(gold_standard_path)
        
    def load_gold_standard(self, path):
        with open(path, 'r') as f:
            data = json.load(f)
        
        unique_risks = {}
        for item in data:
            cat = item['category']
            if cat not in unique_risks:
                unique_risks[cat] = item['nli_hypothesis']
        
        print(f"Loaded {len(unique_risks)} unique risk definitions from JSON.")
        return unique_risks

    def detect_risks(self, pdf_chunks, threshold=0.50, top_k=3):
        
        chunk_texts = [c['text'] for c in pdf_chunks]
        chunk_ids = [c['id'] for c in pdf_chunks]

        # Vectorize
        risk_embeddings = self.model.encode(list(self.gold_standard.values()))
        chunk_embeddings = self.model.encode(chunk_texts)
        
        # Calculate Similarity
        similarity_matrix = cosine_similarity(risk_embeddings, chunk_embeddings)
        
        results = []
        risk_categories = list(self.gold_standard.keys())
        risk_definitions = list(self.gold_standard.values())
        
        # Iterate each Risk Category
        for r_idx, category in enumerate(risk_categories):
            scores = similarity_matrix[r_idx]
            
            indexed_scores = list(enumerate(scores))
            
            indexed_scores.sort(key=lambda x: x[1], reverse=True)
            
            count = 0
            for c_idx, score in indexed_scores:
                if score < threshold:
                    break
                    
                results.append({
                    "risk_category": category,
                    "risk_definition": risk_definitions[r_idx],
                    "chunk_id": chunk_ids[c_idx],
                    "chunk_text": chunk_texts[c_idx],
                    "similarity_score": float(score)
                })
                
                # count += 1
                # if count >= top_k:
                #     break

        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results

if __name__ == "__main__":
    pdf_filename = "contract.pdf"
    json_filename = "synthetic_gold_standard_with_nli.json"
    
    ingestor = ContractIngestor(chunk_size=400, chunk_overlap=100)
    pdf_chunks = ingestor.process_contract(pdf_filename)
    
    if pdf_chunks:
        try:
            detector = RiskDetector(json_filename)
            matches = detector.detect_risks(pdf_chunks, threshold=0.75)
            
            print(f"\n\n{'='*60}")
            print(f"Found {len(matches)} Potential Risks")
            print(f"{'='*60}\n")
            
            for m in matches:
                print(f"RISK TYPE: {m['risk_category']}")
                print(f"   Confidence: {int(m['similarity_score'] * 100)}%")
                print(f"   Clause Found: \"...{m['chunk_text'][:200].replace(chr(10), ' ')}...\"") # clean newlines for display
                print("-" * 50)
                
        except Exception as e:
            print(f"\n[ERROR] {e}")
            print("Ensure your JSON file is in the same folder!")
