import pandas as pd
from openai import OpenAI
import json
import time
import os

OPENROUTER_API_KEY = ""

# Initialize Client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

MODEL_NAME = "amazon/nova-2-lite-v1:free" 


#HARDCODED CONTRACT NLI MAP
def load_nli_hypotheses():
    print("Using hardcoded ContractNLI hypotheses map...")
    return {
        "Termination For Convenience": "Party B may terminate this Agreement for convenience.",
        "Uncapped Liability": "Party A's liability for breach of this Agreement is uncapped.",
        "Non-Compete": "Party A shall not compete with Party B."
    }


PROMPTS = {
    "Termination For Convenience": """
        You are a legal expert.
        RISKY CLAUSE: "{risky_text}"
        OFFICIAL RISK DEFINITION: "{hypothesis}"
        
        TASK:
        1. Rewrite this clause so it CONTRADICTS the risk definition above.
        2. The new clause must require MUTUAL NOTICE (e.g., 30 days) or valid cause.
        
        RETURN JSON ONLY: {{"safe_clause": "...", "explanation": "..."}}
    """,
    "Uncapped Liability": """
        You are a legal expert.
        RISKY CLAUSE: "{risky_text}"
        OFFICIAL RISK DEFINITION: "{hypothesis}"
        
        TASK:
        1. Rewrite this clause so it CONTRADICTS the risk definition above.
        2. The new clause must state a SPECIFIC MONETARY CAP (e.g., 'limited to the fees paid...').
        
        RETURN JSON ONLY: {{"safe_clause": "...", "explanation": "..."}}
    """,
    "Non-Compete": """
        You are a legal expert.
        RISKY CLAUSE: "{risky_text}"
        OFFICIAL RISK DEFINITION: "{hypothesis}"
        
        TASK:
        1. Rewrite this clause so it CONTRADICTS the risk definition above.
        2. The new clause must be NARROWLY TAILORED (limit time/geography) or removed entirely.
        
        RETURN JSON ONLY: {{"safe_clause": "...", "explanation": "..."}}
    """
}


def clean_text_input(text):
    text = str(text).strip()
    if text.startswith("['") and text.endswith("']"):
        return text[2:-2]
    return text

def clean_json_response(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"): lines = lines[1:]
        if lines[-1].startswith("```"): lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()

def llm_call(prompt_type, risky_text, nli_map, retries=3):
    official_hypothesis = nli_map.get(prompt_type, "Standard Risk")
    prompt_template = PROMPTS[prompt_type]
    final_prompt = prompt_template.format(risky_text=risky_text, hypothesis=official_hypothesis)
    
    attempt = 0
    while attempt < retries:
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a helpful legal AI assistant that outputs strictly valid JSON."},
                    {"role": "user", "content": final_prompt}
                ],
                temperature=0.2,
            )
            
            raw_content = response.choices[0].message.content
            if not raw_content:
                return None
            
            return json.loads(clean_json_response(raw_content))

        except Exception as e:
            error_msg = str(e)
            print(f"    [API Error]: {error_msg}")
            
            time.sleep(5)
            attempt += 1
            
    return None

def process_dataset(df, category_name, column_name, nli_map):
    synthetic_data = []
    print(f"\nProcessing {category_name}")
    
    for index, row in df.iterrows():
        if column_name not in row:
            continue
            
        risky_text = clean_text_input(row[column_name])
        
        # Skip garbage rows
        if len(risky_text) < 20: 
            continue

        print(f"  > Row {index}...", end="", flush=True)
        result = llm_call(category_name, risky_text, nli_map)
        
        if result:
            entry = {
                "id": f"{category_name}_{index}",
                "category": category_name,
                "nli_hypothesis": nli_map.get(category_name, "N/A"),
                "risky_clause": risky_text,
                "safe_clause": result.get("safe_clause"),
                "risk_explanation": result.get("explanation")
            }
            synthetic_data.append(entry)
            print(" Done.")
        else:
            print(" Skipped.")
            
        time.sleep(1) 

    return synthetic_data

if __name__ == "__main__":
    nli_map = load_nli_hypotheses()

    files_map = {
        "Termination For Convenience": "termination_full_data.csv",
        "Uncapped Liability": "liability_full_data.csv",
        "Non-Compete": "non_compete_full_data.csv"
    }
    

    for label, f in files_map.items():
        if not os.path.exists(f):
            print(f"CRITICAL: Missing file '{f}'")
            exit()

    all_data = []
    
    # Termination
    print("\nLoading Termination Data...")
    try:
        term_df = pd.read_csv(files_map["Termination For Convenience"]).head(17)
        all_data.extend(process_dataset(term_df, "Termination For Convenience", "Termination For Convenience", nli_map))
    except Exception as e:
        print(f"Error loading Termination CSV: {e}")

    # Liability
    print("\nLoading Liability Data...")
    try:
        liab_df = pd.read_csv(files_map["Uncapped Liability"]).head(16)
        all_data.extend(process_dataset(liab_df, "Uncapped Liability", "Uncapped Liability", nli_map))
    except Exception as e:
        print(f"Error loading Liability CSV: {e}")

    # Non-Compete
    print("\nLoading Non-Compete Data...")
    try:
        comp_df = pd.read_csv(files_map["Non-Compete"]).head(17)
        all_data.extend(process_dataset(comp_df, "Non-Compete", "Non-Compete", nli_map))
    except Exception as e:
        print(f"Error loading Non-Compete CSV: {e}")


    output_file = 'synthetic_gold_standard_with_nli.json'
    if all_data:
        with open(output_file, 'w') as f:
            json.dump(all_data, f, indent=4)
        print(f"\n{len(all_data)} items. Saved to {output_file}")
    else:
        print("\nFAILED.")