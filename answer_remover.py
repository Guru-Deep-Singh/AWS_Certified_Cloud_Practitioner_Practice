import os
import re

def remove_answers_and_save_separately(input_dir, output_dir, answers_dir):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(answers_dir, exist_ok=True)

    details_pattern = re.compile(r'<details[\s\S]*?</details>', re.MULTILINE)

    for filename in os.listdir(input_dir):
        if filename.endswith('.md'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            answers_path = os.path.join(answers_dir, filename)

            with open(input_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Find the title (first header line)
            title_match = re.search(r'^#\s+.*', content, re.MULTILINE)
            title = title_match.group(0).strip() if title_match else ''

            # Split the content into parts: ['', '1', 'Question1...', '2', 'Question2...', ...]
            parts = re.split(r'(?m)^(\d+)\.\s', content)

            cleaned_content = ''
            answers = []

            for i in range(1, len(parts), 2):
                q_num = parts[i]
                q_text = parts[i+1]

                # Extract the answer inside <details>
                answer_match = re.search(r'Correct answer:\s*(.*)', q_text)
                answer = answer_match.group(1).strip() if answer_match else 'NOT FOUND'

                answers.append((q_num, answer))

                # Remove the <details> section
                q_text_cleaned = re.sub(details_pattern, '', q_text).strip()

                # Rebuild the question with the original number
                cleaned_content += f"{q_num}. {q_text_cleaned}\n\n"

            # Save cleaned markdown (with original question numbers)
            with open(output_path, 'w', encoding='utf-8') as file:
                if title:
                    file.write(f"{title}\n\n")
                file.write(cleaned_content.strip())

            # Save extracted answers (with original question numbers and title)
            with open(answers_path, 'w', encoding='utf-8') as file:
                if title:
                    file.write(f"{title}\n\n")
                for q_num, answer in answers:
                    file.write(f"{q_num}. {answer}\n")

            print(f"Processed {filename} -> {output_path} and {answers_path}")

if __name__ == "__main__":
    input_directory = "."
    output_directory = "./output_md_files"
    answers_directory = "./answers_md_files"
    remove_answers_and_save_separately(input_directory, output_directory, answers_directory)
