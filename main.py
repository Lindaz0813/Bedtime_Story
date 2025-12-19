import os
import openai
import re
import json

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

"""

def call_model(prompt: str, max_tokens=3000, temperature=0.1) -> str:
    openai.api_key = os.getenv("OPENAI_API_KEY") # please use your own openai api key here.
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message["content"]  # type: ignore


def load_prompt(filename: str) -> str:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise RuntimeError(f"Prompt file not found: {filename}")
    
def storyteller_prompt(user_request: str) -> str:
    template = load_prompt("story_teller_prompt.txt")
    return template.format(user_request=user_request)

def judge_prompt(story: str) -> str:
    template = load_prompt("judge_prompt.txt")
    return template.replace("{story}", story)

def revision_prompt(story: str, feedback: str) -> str:
    template = load_prompt("revision_prompt.txt")
    return template.format(story=story, feedback=feedback)

def summary_prompt(story: str) -> str:
    template = load_prompt("summary_prompt.txt")
    return template.format(story=story)



def make_filename_from_input(user_input: str, max_words: int = 5) -> str:
    words = user_input.strip().split()[:max_words]
    base = "_".join(words)
    base = re.sub(r"[^\w_]", "", base)  # remove punctuation
    return base

def human_review():
    response = input("\nDo you approve this story? (yes/no): ").strip().lower()
    if response in ["yes", "y"]:
        return True
    else:
        feedback = input("Please provide your feedback for revision: ").strip()
        return feedback

def formatted_judgment_json_to_str(judgment_json):
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


def safe_load_json(text):
    # Remove ```json ... ``` or ``` ... ``` if present
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.DOTALL)
    text = re.sub(r"^```|\s*```$", "", text.strip(), flags=re.DOTALL)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print("JSON decode error:", e)
        print("Text was:", text)
        return None

def ensure_folder(path):
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

def judge_process(folder_path, formatted_judgment, initial_story):
    story = initial_story
    max_iterations = 3
    all_human_feedback = ""

    for i in range(max_iterations):
        print("\n--- Current Story ---\n")
        print(story)

        human_result = human_review()
        if human_result is True:
            print("\nHuman approved the story. Process finished.")
            break

        all_human_feedback = all_human_feedback + "\n" + human_result

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

def main():
    user_input = input("What kind of story do you want to hear?").strip()
    if not user_input:
        user_input = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."

    filename = make_filename_from_input(user_input)
    folder_path = f"outputs/{filename}"
    ensure_folder(folder_path)

    # Step 1: Generate story
    story = call_model(storyteller_prompt(user_input))
    print("\n--- Initial Story ---\n")
    print(story)
    story_path = f"{folder_path}/{filename}_initial.txt"
    save_text(story, story_path)

    # Step 2: AI Judge
    judgment_text = call_model(judge_prompt(story), temperature=0.2)
    judgment_json = safe_load_json(judgment_text)
    ai_judgment_filename = f"{folder_path}/_ai_judgment_0.json"
    save_json(judgment_json, ai_judgment_filename)

    formatted_judgment = formatted_judgment_json_to_str(judgment_json)

    # Step 3: Revision loop
    final_story = judge_process(folder_path, formatted_judgment, story)

    story_path = f"{folder_path}/{filename}_final.txt"
    save_text(final_story, story_path)

    # Step 4: Summary
    summary = call_model(summary_prompt(final_story), temperature=0.3)
    print("\n--- Summary & Lesson ---\n")
    print(summary)
    summary_path = f"{folder_path}/summary.txt"
    save_text(summary, summary_path)

if __name__ == "__main__":
    main()