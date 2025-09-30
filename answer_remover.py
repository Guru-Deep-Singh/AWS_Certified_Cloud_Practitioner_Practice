
import os
import re

DETAILS_BLOCK_RE = re.compile(r"<details[^>]*>([\s\S]*?)</details>", re.IGNORECASE)
ANSWER_LINE_RE = re.compile(r"(?im)^\s*Correct\s*Answer(?:s)?\s*:\s*(.+?)\s*$")
QUESTION_SPLIT_RE = re.compile(r"(?m)^\s*(\d+)\.\s")
FRONT_MATTER_RE = re.compile(r"^---\n[\s\S]*?\n---\s*", re.MULTILINE)

def normalize_answer(ans: str) -> str:
    cleaned = re.sub(r"\band\b", ",", ans, flags=re.IGNORECASE).strip()
    parts = re.findall(r"[A-E]", cleaned, flags=re.IGNORECASE)
    if parts:
        return ", ".join([p.upper() for p in parts])
    return cleaned

def remove_answers_and_save_separately(input_dir, output_dir, answers_dir, keep_front_matter=False):
    """
    keep_front_matter=False removes YAML front matter from BOTH output files (questions + answers).
    Set True if you want to preserve it.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(answers_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if not filename.endswith(".md"):
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        answers_path = os.path.join(answers_dir, filename)

        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        fm_match = FRONT_MATTER_RE.match(content)
        front_matter = fm_match.group(0) if fm_match else ""
        body = content[len(front_matter):] if fm_match else content

        # Title (kept in outputs)
        title_match = re.search(r"(?m)^#\s+.*", body)
        title = title_match.group(0).strip() if title_match else ""

        parts = QUESTION_SPLIT_RE.split(body)

        cleaned_questions = []
        answers = []
        q_counter = 1

        for i in range(1, len(parts), 2):
            q_text = parts[i+1]

            answer_value = "NOT FOUND"
            details_blocks = DETAILS_BLOCK_RE.findall(q_text)
            for db in details_blocks:
                m = ANSWER_LINE_RE.search(db)
                if m:
                    answer_value = normalize_answer(m.group(1))
                    break
            if answer_value == "NOT FOUND":
                m2 = ANSWER_LINE_RE.search(q_text)
                if m2:
                    answer_value = normalize_answer(m2.group(1))

            answers.append((q_counter, answer_value))

            q_text_cleaned = DETAILS_BLOCK_RE.sub("", q_text)
            q_text_cleaned = re.sub(r"\n{3,}", "\n\n", q_text_cleaned).strip()

            cleaned_questions.append(f"{q_counter}. {q_text_cleaned}")
            q_counter += 1

        # Write cleaned markdown (QUESTIONS)
        with open(output_path, "w", encoding="utf-8") as f:
            # YAML front matter intentionally omitted when keep_front_matter is False
            if keep_front_matter and front_matter:
                f.write(front_matter)
                if not front_matter.endswith("\n"):
                    f.write("\n")
            if title:
                f.write(f"{title}\n\n")
            if cleaned_questions:
                f.write("\n\n".join(cleaned_questions).strip())
                f.write("\n")

        # Write answers markdown (ANSWERS)
        with open(answers_path, "w", encoding="utf-8") as f:
            # YAML front matter intentionally omitted when keep_front_matter is False
            if keep_front_matter and front_matter:
                f.write(front_matter)
                if not front_matter.endswith("\n"):
                    f.write("\n")
            if title:
                f.write(f"{title}\n\n")
            for num, ans in answers:
                f.write(f"{num}. {ans}\n")

        print(f"Processed {filename} -> {output_path} and {answers_path}")

if __name__ == "__main__":
    input_directory = "."
    output_directory = "./output_md_files"
    answers_directory = "./answers_md_files"
    # By default, DO NOT keep front matter in outputs
    remove_answers_and_save_separately(input_directory, output_directory, answers_directory, keep_front_matter=False)
