from helpers import *

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

I would like to add more evaluation metrics and get some statistics on how AI ranks the stories. 
Prepare a bigger set of test prompts and run to evaluate robustness.
Check for edge cases, e.g., long stories, abstract topics, or unusual characters.
Build a simple web interface or Jupyter notebook UI.

"""

def main():

    categories = [
        ("Animal Adventures 🐾", "Emphasize anthropomorphic animals, nature settings, and friendship-based conflicts. Use simple dialogue."),
        ("Magic & Imagination ✨", "Include a gentle magical element. Encourage imaginative discoveries and safe 'magical mishaps.'"),
        ("Everyday Life & Lessons 🏡", "Focus on small problems relatable to 5–10-year-olds. Highlight empathy, kindness, and problem-solving."),
        ("Emotional Comfort & Coping 💛", "Include feelings, reassurance, calming routines, and positive emotional resolution."),
        ("Curiosity & Exploration 🔍", "Emphasize discovery, curiosity, and small adventures. Reward exploration and gentle problem-solving."),
        ("Cute & Wholesome 🐰", "Maximize heartwarming and adorable elements. Emphasize gentle humor, affection, and safe settings.")
    ]
    # Display categories
    print("Please select the type of story you want:")
    for i, (name, _) in enumerate(categories, start=1):
        print(f"{i}. {name}")

    # Prompt user to select by number
    selection = input("Enter the number of your choice (default 1): ").strip()
    try:
        selection_num = int(selection)
        if 1 <= selection_num <= len(categories):
            selected_category_name, selected_category_instructions = categories[selection_num - 1]
        else:
            selected_category_name, selected_category_instructions = categories[0]  # default
    except ValueError:
        selected_category_name, selected_category_instructions = categories[0]  # default

    print(f"\nYou selected: {selected_category_name}\n")

    # User story request
    user_input = input("What kind of story do you want to hear? ").strip()
    if not user_input:
        user_input = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."

    filename = make_filename_from_input(user_input)
    folder_path = f"outputs/{filename}"
    ensure_folder(folder_path)

    # Step 1: Generate story
    story = call_model(storyteller_prompt(selected_category_name, 
                                          selected_category_instructions, user_input))
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