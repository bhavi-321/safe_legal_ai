// Configure your FastAPI backend URL here
// For local development: "http://localhost:8000"
// For production: update to your deployed API URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export interface RiskItem {
  chunk_text: string;
  risk_type: string;
  similarity_score: number;
  suggested_clause?: string;
  explanation?: string;
}

export interface AnalysisResponse {
  filename: string;
  num_chunks: number;
  num_risks: number;
  risks: RiskItem[];
  status: string;
  message?: string;
}

export interface ProcessedClause {
  id: number;
  title: string;
  originalText: string;
  suggestedText: string;
  riskLevel: "high" | "medium" | "low";
  confidenceScore: number;
  explanation: string;
}

// Map similarity score to risk level
function getRiskLevel(score: number): "high" | "medium" | "low" {
  if (score >= 0.85) return "high";
  if (score >= 0.75) return "medium";
  return "low";
}

// Transform API response to frontend format
export function processApiResponse(response: AnalysisResponse): ProcessedClause[] {
  return response.risks.map((risk, index) => ({
    id: index + 1,
    title: risk.risk_type || `Risk Clause ${index + 1}`,
    originalText: risk.chunk_text,
    suggestedText: risk.suggested_clause || "Review this clause with legal counsel for a safer alternative.",
    riskLevel: getRiskLevel(risk.similarity_score),
    confidenceScore: Math.round(risk.similarity_score * 100),
    explanation: risk.explanation || `This clause has been flagged as potentially risky based on pattern matching with known problematic contract terms.`,
  }));
}

export async function analyzeContract(file: File): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/analyze-contract`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Analysis failed with status ${response.status}`);
  }

  return response.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
