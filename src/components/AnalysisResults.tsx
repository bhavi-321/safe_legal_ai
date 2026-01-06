import { AlertTriangle, CheckCircle, FileText, TrendingUp } from "lucide-react";
import ClauseCard from "./ClauseCard";
import { Button } from "./ui/button";

interface AnalysisResult {
  id: number;
  title: string;
  originalText: string;
  suggestedText: string;
  riskLevel: "high" | "medium" | "low";
  confidenceScore: number;
  explanation: string;
}

interface AnalysisResultsProps {
  results: AnalysisResult[];
  fileName: string;
  onNewAnalysis: () => void;
}

const AnalysisResults = ({ results, fileName, onNewAnalysis }: AnalysisResultsProps) => {
  const highRiskCount = results.filter((r) => r.riskLevel === "high").length;
  const mediumRiskCount = results.filter((r) => r.riskLevel === "medium").length;
  const lowRiskCount = results.filter((r) => r.riskLevel === "low").length;

  const overallScore = Math.round(
    100 - (highRiskCount * 15 + mediumRiskCount * 8 + lowRiskCount * 2)
  );

  return (
    <div className="w-full max-w-4xl mx-auto animate-fade-in">
      {/* Summary Header */}
      <div className="bg-card rounded-2xl border border-border shadow-medium p-8 mb-8">
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
              <FileText className="w-4 h-4" />
              <span>{fileName}</span>
            </div>
            <h2 className="font-heading text-2xl font-bold text-foreground">
              Analysis Complete
            </h2>
          </div>
          <Button variant="outline" onClick={onNewAnalysis}>
            New Analysis
          </Button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-muted/50 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-primary" />
              <span className="text-sm text-muted-foreground">Safety Score</span>
            </div>
            <p className="text-3xl font-bold text-foreground">{overallScore}%</p>
          </div>
          
          <div className="p-4 bg-risk-high/5 rounded-xl border border-risk-high/20">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-risk-high" />
              <span className="text-sm text-muted-foreground">High Risk</span>
            </div>
            <p className="text-3xl font-bold text-risk-high">{highRiskCount}</p>
          </div>

          <div className="p-4 bg-risk-medium/5 rounded-xl border border-risk-medium/20">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-risk-medium" />
              <span className="text-sm text-muted-foreground">Medium Risk</span>
            </div>
            <p className="text-3xl font-bold text-risk-medium">{mediumRiskCount}</p>
          </div>

          <div className="p-4 bg-risk-low/5 rounded-xl border border-risk-low/20">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-4 h-4 text-risk-low" />
              <span className="text-sm text-muted-foreground">Low Risk</span>
            </div>
            <p className="text-3xl font-bold text-risk-low">{lowRiskCount}</p>
          </div>
        </div>
      </div>

      {/* Flagged Clauses */}
      <div className="space-y-4">
        <h3 className="font-heading text-xl font-semibold text-foreground mb-4">
          Flagged Clauses ({results.length})
        </h3>
        {results.map((clause, index) => (
          <ClauseCard key={clause.id} clause={clause} index={index} />
        ))}
      </div>
    </div>
  );
};

export default AnalysisResults;
