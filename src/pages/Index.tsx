import { useState } from "react";
import Header from "@/components/Header";
import HeroSection from "@/components/HeroSection";
import DocumentUpload from "@/components/DocumentUpload";
import AnalysisResults from "@/components/AnalysisResults";

// Mock data for demonstration
const mockResults = [
  {
    id: 1,
    title: "Unlimited Liability Clause",
    originalText: "The Client agrees to indemnify and hold harmless the Company against any and all claims, damages, losses, costs, and expenses, without any limitation, arising from the Client's use of the services.",
    suggestedText: "The Client agrees to indemnify and hold harmless the Company against claims directly caused by the Client's gross negligence or willful misconduct, with total liability capped at the fees paid under this agreement in the preceding 12 months.",
    riskLevel: "high" as const,
    confidenceScore: 94,
    explanation: "This clause exposes you to unlimited financial liability. The phrase 'without any limitation' is particularly concerning as it could lead to disproportionate damages.",
  },
  {
    id: 2,
    title: "Unilateral Modification Rights",
    originalText: "The Company reserves the right to modify these terms at any time without prior notice. Continued use of services constitutes acceptance of modified terms.",
    suggestedText: "The Company may modify these terms with 30 days written notice to the Client. Material changes require Client's written consent. Client may terminate within 15 days of receiving notice of changes.",
    riskLevel: "high" as const,
    confidenceScore: 89,
    explanation: "Allows the other party to change contract terms without your knowledge or consent, potentially altering your obligations significantly.",
  },
  {
    id: 3,
    title: "Broad Intellectual Property Transfer",
    originalText: "All work product, ideas, inventions, and intellectual property created during the term of this agreement shall become the exclusive property of the Company.",
    suggestedText: "Work product specifically created for and directly related to the contracted services shall be assigned to the Company. Pre-existing intellectual property and work outside the scope of services remains with the Creator.",
    riskLevel: "medium" as const,
    confidenceScore: 76,
    explanation: "Overly broad IP transfer that could include unrelated inventions or pre-existing work. Should be limited to work directly related to the engagement.",
  },
  {
    id: 4,
    title: "Non-Compete Duration",
    originalText: "For a period of two (2) years following termination, the Client shall not engage in any business that competes with the Company within any geographic region.",
    suggestedText: "For a period of twelve (12) months following termination, the Client shall not directly compete with the Company's specific services within the metropolitan areas where the Company actively operates.",
    riskLevel: "medium" as const,
    confidenceScore: 72,
    explanation: "The two-year duration and unlimited geographic scope may be overly restrictive and potentially unenforceable in many jurisdictions.",
  },
  {
    id: 5,
    title: "Auto-Renewal Terms",
    originalText: "This agreement shall automatically renew for successive one-year terms unless terminated by either party.",
    suggestedText: "This agreement shall automatically renew for successive one-year terms unless either party provides written notice of non-renewal at least 60 days prior to the renewal date.",
    riskLevel: "low" as const,
    confidenceScore: 65,
    explanation: "While auto-renewal is standard, lacking a clear cancellation window could lead to unintended commitments.",
  },
];

const Index = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<typeof mockResults | null>(null);
  const [fileName, setFileName] = useState("");

  const handleAnalyze = async (file: File) => {
    setIsAnalyzing(true);
    setFileName(file.name);
    
    // Simulate API call - replace with actual FastAPI call
    await new Promise((resolve) => setTimeout(resolve, 3000));
    
    setResults(mockResults);
    setIsAnalyzing(false);
  };

  const handleNewAnalysis = () => {
    setResults(null);
    setFileName("");
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-6 pt-32 pb-20">
        {!results ? (
          <>
            <HeroSection />
            <DocumentUpload onAnalyze={handleAnalyze} isAnalyzing={isAnalyzing} />
          </>
        ) : (
          <AnalysisResults
            results={results}
            fileName={fileName}
            onNewAnalysis={handleNewAnalysis}
          />
        )}
      </main>

      {/* Background decoration */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-accent/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-primary/5 rounded-full blur-3xl" />
      </div>
    </div>
  );
};

export default Index;
