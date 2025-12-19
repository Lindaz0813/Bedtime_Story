import os
import openai
import re

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
    return template.format(story=story)

def revision_prompt(story: str, feedback: str) -> str:
    template = load_prompt("revision_prompt.txt")
    return template.format(story=story, feedback=feedback)



def make_filename_from_input(user_input: str, max_words: int = 5) -> str:
    words = user_input.strip().split()[:max_words]
    base = "_".join(words)
    base = re.sub(r"[^\w_]", "", base)  # remove punctuation
    return f"{base}.txt"

def main():
    user_input = input("What kind of story do you want to hear?").strip()

    example_requests = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."

    if not user_input:
        user_input = example_requests

    # Step 1: Generate story
    story = call_model(storyteller_prompt(user_input))
    print("\n--- Initial Story ---\n")
    print(story)

    # Step 2: AI Judge
    judgment = call_model(judge_prompt(story), temperature=0.2)
    print("\n--- AI Judge Evaluation ---\n")
    print(judgment)

    # Step 3: Revision loop with user feedback
    final_story = story
    max_iterations = 3
    for i in range(max_iterations):
        print("\n--- Current Story ---\n")
        print(final_story)

        user_feedback = input("\nDo you want any changes to this story? (type your request or 'no'): ").strip()
        if user_feedback.lower() in ["no", "n", ""]:
            break  # user approves

        # Combine AI judgment + user feedback for revision
        combined_feedback = f"{judgment}\nUser feedback: {user_feedback}"
        final_story = call_model(revision_prompt(final_story, combined_feedback), temperature=0.6)
        print("\n--- Revised Story ---\n")
        print(final_story)

    # Step 4: Save to file
    filename = make_filename_from_input(user_input)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_story)

    print(f"\nStory saved to {filename}")

if __name__ == "__main__":
    main()