export async function analyzeContract(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    "http://localhost:8000/analyze-contract",
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Failed to analyze contract");
  }

  return response.json();
}