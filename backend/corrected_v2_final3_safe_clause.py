from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from dotenv import load_dotenv
from langfuse import get_client
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

# Initialize Langfuse client
langfuse = get_client()
# langfuse = None
# langfuse = None  # Disable Langfuse for now

# --- NEW: Initialize OpenRouter Client ---
# Make sure OPENROUTER_API_KEY is in your .env file
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    # api_key=os.getenv("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"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Define the model you want to use (e.g., 'google/gemini-2.0-flash-exp:free' or similar)
# You can change this to "gpt-oss-120b" if that specific ID exists on OpenRouter
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
        "version": "0.1"
    }
@app.post("/analyze-contract")
async def analyze_contract(file: UploadFile = File(...)):
    """
    Upload a contract PDF and get detected legal risks.
    
    Args:
        file: PDF file to analyze
        
    Returns:
        JSON response with detected risks
    """
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    pdf_path = None
    
    try:
        # Create a trace for this contract analysis
        with langfuse.start_as_current_observation(
            as_type="span",
            name="analyze_contract",
            input={"filename": file.filename}
        ) as trace_span:
            
            # Save uploaded PDF temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                contents = await file.read()
                if not contents:
                    raise HTTPException(
                        status_code=400,
                        detail="Uploaded file is empty"
                    )
                tmp.write(contents)
                pdf_path = tmp.name

            # Ingest PDF → chunks
            with langfuse.start_as_current_observation(
                as_type="span",
                name="ingestion"
            ) as ingestion_span:
                ingestor = ContractIngestor(chunk_size=600, chunk_overlap=150)
                chunks = ingestor.process_contract(pdf_path)
                ingestion_span.update(output={"num_chunks": len(chunks)})

            if not chunks:
                result = {
                    "filename": file.filename,
                    "num_chunks": 0,
                    "num_risks": 0,
                    "risks": [],
                    "message": "No text could be extracted from the PDF."
                }
                trace_span.update(output=result)
                return JSONResponse(status_code=200, content=result)

            # Detect risks
            with langfuse.start_as_current_observation(
                as_type="span",
                name="risk_detection"
            ) as detection_span:
                detector = RiskDetector(
                    "H:\\proj\\Legality_AI\\synthetic_gold_standard_with_nli.json"
                )
                risks = detector.detect_risks(chunks, threshold=0.75)
                detection_span.update(output={"num_risks": len(risks)})
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

            # for risk in risks:
            #     # Call OpenRouter for each detected risk
            #     suggestion = generate_safe_rewrite(
            #         risky_text=risk['chunk_text'], 
            #         risk_type=risk['risk_category']
            #     )
            #     # Add the 'suggested_clause' field which frontend expects
            #     risk['suggested_clause'] = suggestion
            # Return structured response
            response = {
                "filename": file.filename,
                "num_chunks": len(chunks),
                "num_risks": len(risks),
                "risks": risks,
                "status": "success"
            }
            
            # Update trace with final output
            trace_span.update(output=response)
            
            return response

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
        langfuse.flush()

@app.get("/health")
async def health_check():
    """Check if all required files and dependencies are available"""
    dataset_path = "H:\\proj\\Legality_AI\\synthetic_gold_standard_with_nli.json"
    
    # Test Langfuse connection
    langfuse_ok = False
    try:
        langfuse.auth_check()
        langfuse_ok = True
    except Exception as e:
        print(f"Langfuse auth check failed: {e}")
    
    return {
        "status": "healthy",
        "langfuse_connected": langfuse_ok,
        "dataset_exists": os.path.exists(dataset_path),
        "dataset_path": dataset_path
    }


@app.on_event("shutdown")
async def shutdown_event():
    """Ensure all Langfuse data is flushed on shutdown"""
    langfuse.flush()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)