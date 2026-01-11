from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from dotenv import load_dotenv
# from langfuse import Langfuse
import traceback
from openai import OpenAI 

from ip_mod_api import ContractIngestor
from vector_search import RiskDetector
from clause_policy import decide_clause_action, ClauseAction, validate_rewrite_output

FORBIDDEN_TERMS = [
    "liability shall be limited",
    "in no event shall",
    "consequential damages",
    "punitive damages",
    "$",
    "cap",
    "fees paid"
]

# Load environment variables
load_dotenv()


# try:
#     langfuse = Langfuse()
# except Exception as e:
#     print(f"Warning: Langfuse client failed to initialize: {e}")
langfuse = None

# --- NEW: Initialize OpenRouter Client ---
# Make sure OPENROUTER_API_KEY is in your .env file
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Define the model you want to use
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct:free" 

# Initialize FastAPI app
app = FastAPI(
    title="Legality AI - Contract Risk Detector",
    description="Detects risky clauses in contracts using embeddings",
    version="0.1"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL MODEL INITIALIZATION (Fixes Timeout Issue) ---
# We initialize the model ONCE when the server starts, not per request.
print("--- INITIALIZING AI MODEL (This may take a minute) ---")
detector = None
DATASET_PATH = "dataset/synthetic_gold_standard_with_nli.json" # Use forward slash for Linux/Render

try:
    if os.path.exists(DATASET_PATH):
        detector = RiskDetector(DATASET_PATH)
        print("RiskDetector Model initialized successfully.")
    else:
        print(f"CRITICAL ERROR: Dataset not found at {DATASET_PATH}")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to load RiskDetector: {e}")
    traceback.print_exc()

# ---------------------------------------------------------

def is_safe_rewrite(original: str, rewritten: str) -> bool:
    lower = rewritten.lower()
    return not any(term in lower for term in FORBIDDEN_TERMS)

# --- NEW: Helper Function to Generate Safe Clause ---
def generate_safe_rewrite(risky_text: str, risk_type: str) -> str:
    """
    Uses OpenRouter to rewrite a risky clause.
    """
    prompt = f"""
    You are a senior legal expert.
    You are rewriting a contract clause for clarity ONLY.

STRICT RULES:
- Do NOT add new legal concepts
- Do NOT add liability caps, damages, numbers, or exclusions
- Do NOT remove or limit existing rights
- Do NOT introduce new obligations
- Preserve the original legal meaning
- Do NOT add conversational filler (e.g., "Here is the rewrite").
- Output ONLY the rewritten clause text.

TASK:
Rewrite the clause below to be clearer and more balanced in wording ONLY.

Clause:
{risky_text}"""
    
    try:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful legal assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, # Keep it deterministic
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Generation Failed: {e}")
        return "Legal review recommended. (generation unavailable)"

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Legality AI - Contract Risk Detector",
        "version": "0.1",
        "model_loaded": detector is not None
    }

@app.post("/analyze-contract")
async def analyze_contract(file: UploadFile = File(...)):
    """
    Upload a contract PDF and get detected legal risks.
    """
    
    # Check if model is loaded
    if detector is None:
        raise HTTPException(
            status_code=500,
            detail="AI Model is not loaded. Please check server logs."
        )

    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    pdf_path = None
    
    try:
        # Create a trace for this contract analysis (Optional check if langfuse is active)
        trace_span = None
        if langfuse:
            trace_span = langfuse.trace(
                name="analyze_contract",
                input={"filename": file.filename}
            )
            
        try:
            # Save uploaded PDF temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                contents = await file.read()
                if not contents:
                    raise HTTPException(status_code=400, detail="Uploaded file is empty")
                tmp.write(contents)
                pdf_path = tmp.name

            # Ingest PDF → chunks
            ingestion_span = None
            if langfuse:
                ingestion_span = trace_span.span(name="ingestion")
            
            ingestor = ContractIngestor(chunk_size=600, chunk_overlap=150)
            chunks = ingestor.process_contract(pdf_path)
            
            if ingestion_span:
                ingestion_span.update(output={"num_chunks": len(chunks)})
                ingestion_span.end()

            if not chunks:
                result = {
                    "filename": file.filename,
                    "num_chunks": 0,
                    "num_risks": 0,
                    "risks": [],
                    "message": "No text could be extracted from the PDF."
                }
                if trace_span:
                    trace_span.update(output=result)
                    trace_span.end()
                return JSONResponse(status_code=200, content=result)

            # Detect risks using GLOBAL detector
            detection_span = None
            if langfuse:
                detection_span = trace_span.span(name="risk_detection")
                
            # --- USE THE GLOBAL DETECTOR HERE ---
            risks = detector.detect_risks(chunks, threshold=0.75)
            
            if detection_span:
                detection_span.update(output={"num_risks": len(risks)})
                detection_span.end()

            # Process Actions & Rewrites
            for risk in risks:
                action = decide_clause_action(
                    risk_category=risk["risk_category"],
                    clause_text=risk["chunk_text"]
                )

                risk["action"] = action

                if action == ClauseAction.REWRITE:
                    rewritten = generate_safe_rewrite(
                        risky_text=risk["chunk_text"],
                        risk_type=risk["risk_category"]
                    )

                    # Validate rewrite safety
                    if not rewritten or not validate_rewrite_output(rewritten):
                        risk["suggested_clause"] = (
                            "Legal review recommended due to potential legal modification."
                        )
                    else:
                        risk["suggested_clause"] = rewritten

                else:
                    # REVIEW ONLY
                    risk["suggested_clause"] = (
                        "Legal review recommended. This clause affects liability, "
                        "damages, or remedies and should not be rewritten automatically."
                    )

            # Return structured response
            response = {
                "filename": file.filename,
                "num_chunks": len(chunks),
                "num_risks": len(risks),
                "risks": risks,
                "status": "success"
            }
            
            if trace_span:
                trace_span.update(output=response)
                trace_span.end()
            
            return response
            
        except Exception as inner_e:
            if trace_span:
                 trace_span.update(level="ERROR", status_message=str(inner_e))
                 trace_span.end()
            raise inner_e

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Required file not found: {str(e)}"
        )
    except Exception as e:
        # Log the full error for debugging
        print(f"Error analyzing contract: {str(e)}")
        print(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing contract: {str(e)}"
        )
    
    finally:
        # Cleanup temp file
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception as e:
                print(f"Warning: Could not delete temporary file {pdf_path}: {e}")
        
        # Flush events to Langfuse (important for short-lived requests)
        if langfuse:
            langfuse.flush()

@app.get("/health")
async def health_check():
    """Check if all required files and dependencies are available"""
    # Use global constant
    dataset_exists = os.path.exists(DATASET_PATH)
    
    # Test Langfuse connection
    langfuse_ok = False
    if langfuse:
        try:
            langfuse.auth_check()
            langfuse_ok = True
        except Exception as e:
            print(f"Langfuse auth check failed: {e}")
    
    return {
        "status": "healthy",
        "langfuse_connected": langfuse_ok,
        "dataset_exists": dataset_exists,
        "dataset_path": DATASET_PATH,
        "model_initialized": detector is not None
    }


@app.on_event("shutdown")
async def shutdown_event():
    """Ensure all Langfuse data is flushed on shutdown"""
    if langfuse:
        langfuse.flush()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


