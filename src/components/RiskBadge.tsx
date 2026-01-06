import { cn } from "@/lib/utils";
import { AlertTriangle, AlertCircle, CheckCircle } from "lucide-react";

interface RiskBadgeProps {
  level: "high" | "medium" | "low";
  score: number;
}

const RiskBadge = ({ level, score }: RiskBadgeProps) => {
  const config = {
    high: {
      icon: AlertTriangle,
      label: "High Risk",
      className: "bg-risk-high/10 text-risk-high border-risk-high/20",
    },
    medium: {
      icon: AlertCircle,
      label: "Medium Risk",
      className: "bg-risk-medium/10 text-risk-medium border-risk-medium/20",
    },
    low: {
      icon: CheckCircle,
      label: "Low Risk",
      className: "bg-risk-low/10 text-risk-low border-risk-low/20",
    },
  };

  const { icon: Icon, label, className } = config[level];

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm font-medium",
        className
      )}
    >
      <Icon className="w-4 h-4" />
      <span>{label}</span>
      <span className="text-xs opacity-75">({score}%)</span>
    </div>
  );
};

export default RiskBadge;
