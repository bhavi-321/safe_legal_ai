import { Shield, Sparkles, Clock, FileSearch } from "lucide-react";

const HeroSection = () => {
  return (
    <div className="text-center mb-12 animate-fade-in">
      <div className="inline-flex items-center gap-2 px-4 py-2 bg-accent/10 text-accent rounded-full text-sm font-medium mb-6">
        <Sparkles className="w-4 h-4" />
        AI-Powered Legal Analysis
      </div>
      
      <h1 className="font-heading text-4xl md:text-5xl lg:text-6xl font-bold text-foreground mb-6 leading-tight">
        Detect Legal Red Flags
        <br />
        <span className="text-gradient">Before You Sign</span>
      </h1>
      
      <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-10">
        Upload your contracts and legal documents. Our AI instantly identifies risky clauses, 
        provides confidence scores, and suggests safer alternatives.
      </p>

      <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-success" />
          <span>Bank-level security</span>
        </div>
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-accent" />
          <span>Analysis in seconds</span>
        </div>
        <div className="flex items-center gap-2">
          <FileSearch className="w-4 h-4 text-primary" />
          <span>All document types</span>
        </div>
      </div>
    </div>
  );
};

export default HeroSection;
