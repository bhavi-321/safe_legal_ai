from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from dotenv import load_dotenv
from langfuse import get_client
import traceback

from ip_mod_api import ContractIngestor
from vector_search import RiskDetector

# Load environment variables
load_dotenv()

# Initialize Langfuse client
langfuse = get_client()

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
                    "H:\proj\Legality_AI\synthetic_gold_standard_with_nli.json"
                )
                risks = detector.detect_risks(chunks, threshold=0.75)
                detection_span.update(output={"num_risks": len(risks)})

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
    dataset_path = "H:\proj\Legality_AI\synthetic_gold_standard_with_nli.json"
    
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


