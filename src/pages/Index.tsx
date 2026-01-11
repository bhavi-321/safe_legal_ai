import { useState } from "react";
import Header from "@/components/Header";
import HeroSection from "@/components/HeroSection";
import DocumentUpload from "@/components/DocumentUpload";
import AnalysisResults from "@/components/AnalysisResults";
import { processApiResponse, ProcessedClause } from "@/services/api";
import { analyzeContract } from "@/services/contractApi";
import { useToast } from "@/hooks/use-toast";

const Index = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<ProcessedClause[] | null>(null);
  const [fileName, setFileName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const handleAnalyze = async (file: File) => {
    setIsAnalyzing(true);
    setFileName(file.name);
    setError(null);
    
    try {
      const response = await analyzeContract(file);
      
      if (response.num_risks === 0) {
        toast({
          title: "Analysis Complete",
          description: response.message || "No risky clauses detected in this document.",
        });
        setResults([]);
      } else {
        const processedResults = processApiResponse(response);
        setResults(processedResults);
        toast({
          title: "Analysis Complete",
          description: `Found ${response.num_risks} potential risk${response.num_risks > 1 ? 's' : ''} in your document.`,
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to analyze document";
      setError(errorMessage);
      toast({
        title: "Analysis Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleNewAnalysis = () => {
    setResults(null);
    setFileName("");
    setError(null);
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-6 pt-32 pb-20">
        {!results ? (
          <>
            <HeroSection />
            <DocumentUpload 
              onAnalyze={handleAnalyze} 
              isAnalyzing={isAnalyzing}
              error={error}
            />
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
