import { useState } from "react";
import { ChevronDown, ChevronUp, ArrowRight, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import RiskBadge from "./RiskBadge";
import { cn } from "@/lib/utils";

interface ClauseCardProps {
  clause: {
    id: number;
    title: string;
    originalText: string;
    suggestedText: string;
    riskLevel: "high" | "medium" | "low";
    confidenceScore: number;
    explanation: string;
  };
  index: number;
}

const ClauseCard = ({ clause, index }: ClauseCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(clause.suggestedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={cn(
        "bg-card rounded-2xl border border-border shadow-soft overflow-hidden transition-all duration-300 hover:shadow-medium animate-slide-up",
      )}
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <div
        className="p-6 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Clause #{clause.id}
              </span>
              <RiskBadge level={clause.riskLevel} score={clause.confidenceScore} />
            </div>
            <h3 className="font-heading text-lg font-semibold text-foreground mb-2">
              {clause.title}
            </h3>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {clause.explanation}
            </p>
          </div>
          <button className="p-2 hover:bg-muted rounded-lg transition-colors">
            {isExpanded ? (
              <ChevronUp className="w-5 h-5 text-muted-foreground" />
            ) : (
              <ChevronDown className="w-5 h-5 text-muted-foreground" />
            )}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="px-6 pb-6 border-t border-border pt-6 animate-fade-in">
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-risk-high" />
                <span className="text-sm font-medium text-foreground">Original Clause</span>
              </div>
              <div className="p-4 bg-risk-high/5 border border-risk-high/20 rounded-xl">
                <p className="text-sm text-foreground leading-relaxed">
                  {clause.originalText}
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-success" />
                <span className="text-sm font-medium text-foreground">Suggested Safe Clause</span>
              </div>
              <div className="p-4 bg-success/5 border border-success/20 rounded-xl relative group">
                <p className="text-sm text-foreground leading-relaxed pr-8">
                  {clause.suggestedText}
                </p>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCopy();
                  }}
                  className="absolute top-3 right-3 p-1.5 hover:bg-success/10 rounded-md transition-colors"
                >
                  {copied ? (
                    <Check className="w-4 h-4 text-success" />
                  ) : (
                    <Copy className="w-4 h-4 text-muted-foreground" />
                  )}
                </button>
              </div>
            </div>
          </div>

          <div className="mt-6 flex items-center justify-center">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <ArrowRight className="w-4 h-4" />
              <span>Click to copy the suggested clause</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClauseCard;
