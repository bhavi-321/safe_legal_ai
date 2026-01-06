import { useState, useCallback } from "react";
import { Upload, FileText, X, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface DocumentUploadProps {
  onAnalyze: (file: File) => void;
  isAnalyzing: boolean;
  error?: string | null;
}

const DocumentUpload = ({ onAnalyze, isAnalyzing, error }: DocumentUploadProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  const validateFile = (file: File): boolean => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setFileError("Only PDF files are supported");
      return false;
    }
    setFileError(null);
    return true;
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    setFileError(null);
  };

  const handleAnalyze = () => {
    if (selectedFile) {
      onAnalyze(selectedFile);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto animate-slide-up">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300",
          isDragging
            ? "border-accent bg-accent/5 scale-[1.02]"
            : "border-border hover:border-primary/50 hover:bg-muted/50",
          selectedFile && "border-success bg-success/5"
        )}
      >
        {selectedFile ? (
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-success/10 flex items-center justify-center">
              <FileText className="w-8 h-8 text-success" />
            </div>
            <div className="flex items-center gap-3">
              <span className="font-medium text-foreground">{selectedFile.name}</span>
              <button
                onClick={clearFile}
                className="p-1 hover:bg-muted rounded-full transition-colors"
              >
                <X className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>
            <p className="text-sm text-muted-foreground">
              {(selectedFile.size / 1024).toFixed(1)} KB
            </p>
          </div>
        ) : (
          <>
            <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6 animate-float">
              <Upload className="w-8 h-8 text-primary" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              Drop your legal document here
            </h3>
            <p className="text-muted-foreground mb-6">
              or click to browse from your computer
            </p>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground">
              <span className="px-2 py-1 bg-muted rounded">PDF</span>
            </div>
          </>
        )}
      </div>

      {/* Error Messages */}
      {(fileError || error) && (
        <div className="mt-4 p-4 bg-destructive/10 border border-destructive/20 rounded-xl flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-destructive shrink-0" />
          <p className="text-sm text-destructive">{fileError || error}</p>
        </div>
      )}

      {selectedFile && (
        <div className="mt-6 flex justify-center">
          <Button
            variant="hero"
            size="xl"
            onClick={handleAnalyze}
            disabled={isAnalyzing}
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Analyzing Document...
              </>
            ) : (
              <>
                Analyze for Red Flags
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
};

export default DocumentUpload;
