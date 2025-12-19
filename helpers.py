import os
import re
import json
import openai

# -------------------------
# OpenAI model helper
# -------------------------
def call_model(prompt: str, max_tokens=3000, temperature=0.1) -> str:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message["content"] 

# -------------------------
# Prompt loaders
# -------------------------
def load_prompt(filename: str) -> str:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise RuntimeError(f"Prompt file not found: {filename}")

def storyteller_prompt(selected_category: str, instructions: str, user_request: str) -> str:
    template = load_prompt("story_teller_prompt.txt")
    return template.format(selected_category=selected_category, 
                           selected_category_instructions=instructions, 
                           user_request=user_request)

def judge_prompt(story: str) -> str:
    template = load_prompt("judge_prompt.txt")
    return template.replace("{story}", story)

def revision_prompt(story: str, feedback: str) -> str:
    template = load_prompt("revision_prompt.txt")
    return template.format(story=story, feedback=feedback)

def summary_prompt(story: str) -> str:
    template = load_prompt("summary_prompt.txt")
    return template.format(story=story)

# -------------------------
# File & folder helpers
# -------------------------
def make_filename_from_input(user_input: str, max_words: int = 5) -> str:
    words = user_input.strip().split()[:max_words]
    base = "_".join(words)
    base = re.sub(r"[^\w_]", "", base)  # remove punctuation
    return base

def ensure_folder(path: str):
    os.makedirs(path, exist_ok=True)
    print(f"Folder '{path}' is ready.")

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Saved JSON to {path}")

def save_text(text, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Saved text to {path}")

# -------------------------
# Human feedback
# -------------------------
def human_review() -> str:
    response = input("\nDo you approve this story? (yes/no): ").strip().lower()
    if response in ["yes", "y"]:
        return "Approved by human"
    else:
        feedback = input("Please provide your feedback for revision: ").strip()
        return feedback

# -------------------------
# JSON helpers
# -------------------------
def formatted_judgment_json_to_str(judgment_json: dict) -> str:
    scores = judgment_json.get("scores", {})
    suggestions = judgment_json.get("suggestions", [])
    weakness = judgment_json.get("weakness", "")

    return "\n".join([
        "Scores:",
        *[f"- {k.replace('_', ' ').capitalize()}: {v}" for k, v in scores.items()],
        "",
        "Suggestions:",
        *[f"- {s}" for s in suggestions],
        "",
        "Weakness:",
        f"- {weakness}"
    ])

def safe_load_json(text: str) -> dict:
    # Remove ```json ... ``` or ``` ... ``` if present
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.DOTALL)
    text = re.sub(r"^```|\s*```$", "", text.strip(), flags=re.DOTALL)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print("JSON decode error:", e)
        print("Text was:", text)
        return None

# -------------------------
# Judge process loop
# -------------------------
def judge_process(folder_path: str, formatted_judgment: str, initial_story: str) -> str:
    story = initial_story
    max_iterations = 3
    all_human_feedback = ""

    for i in range(max_iterations):
        print("\n--- Current Story ---\n")
        print(story)

        human_result = human_review()
        all_human_feedback += "\n" + human_result

        if human_result == "Approved by human":
            print("\nHuman approved the story. Process finished.")
            break

        combined_feedback = f"Judge Feedback: {formatted_judgment}\nHuman feedback: {human_result}"
        story = call_model(revision_prompt(story, combined_feedback), temperature=0.6)

        judgment_text = call_model(judge_prompt(story), temperature=0.2)
        ai_judgment = safe_load_json(judgment_text)

        ai_judgment_filename = f"{folder_path}/_ai_judgment_{i+1}.json"
        save_json(ai_judgment, ai_judgment_filename)

        formatted_judgment = formatted_judgment_json_to_str(ai_judgment)

        print("\n--- AI Re-Judgment ---\n")
        print(formatted_judgment)

    else:
        print("\nMax iterations reached. Final story:")

    story_path = f"{folder_path}/all_human_feedback.txt"
    save_text(all_human_feedback, story_path)
    print(story)
    return story
