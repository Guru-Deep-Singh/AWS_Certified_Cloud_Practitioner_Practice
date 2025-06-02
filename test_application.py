import streamlit as st
import pandas as pd
import re
import os
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

# ---------- File Parsing Utilities ----------

def parse_md_file(md_path):
    with open(md_path, 'r', encoding='utf-8') as file:
        content = "\n".join(line for line in file if not line.strip().startswith("#"))

    question_blocks = re.split(r'\n(?=\d+\.\s)', content)

    questions = []
    for block in question_blocks:
        if not block.strip():
            continue

        lines = block.strip().split('\n')
        q_text = lines[0]
        options = []
        for line in lines[1:]:
            line = line.strip()
            if re.match(r'-\s+[A-Z]\.', line):
                options.append(line[2:].strip())

        multi_select = bool(re.search(r'\b(Choose|Select)\b.*\b(TWO|THREE|FOUR)\b', q_text, re.IGNORECASE))

        questions.append({
            'question': q_text,
            'options': options,
            'multi_select': multi_select
        })

    return questions

def parse_answers_file(answers_path):
    with open(answers_path, 'r', encoding='utf-8') as file:
        lines = [line for line in file if not line.strip().startswith("#")]

    answers = {}
    for line in lines:
        if line.strip() and re.match(r'\d+\.\s', line):
            q_num, ans = line.strip().split('.', 1)
            ans_list = [a.strip() for a in ans.strip().split(',')]
            answers[q_num] = ans_list

    return answers

def extract_option_letter(option_text):
    match = re.match(r'^([A-Z])\.', option_text.strip())
    if match:
        return match.group(1)
    return option_text.strip()

def extract_test_number(filename):
    match = re.search(r'(\d+)(?=\.md$)', filename)
    return int(match.group(1)) if match else float('inf')

# ---------- Streamlit App Main ----------

def main():
    st.title("📚 AWS Certified Cloud Practitioner: Practice Tests!")

    question_dir = "output_md_files"
    answer_dir = "answers_md_files"

    available_tests = sorted([
        f for f in os.listdir(question_dir)
        if f.endswith(".md") and os.path.exists(os.path.join(answer_dir, f))
    ], key=extract_test_number)

    test_selected = st.selectbox("Select a test to take:", available_tests)

    if test_selected:
        md_path = os.path.join(question_dir, test_selected)
        ans_path = os.path.join(answer_dir, test_selected)

        try:
            questions = parse_md_file(md_path)
            correct_answers = parse_answers_file(ans_path)
        except Exception as e:
            st.error(f"❌ Error parsing selected files: {e}")
            return

        st.success(f"Parsed {len(questions)} questions from **{test_selected}**!")

        user_answers = {}
        flags = {}

        for idx, q in enumerate(questions, 1):
            st.markdown(f"**{idx}. {q['question']}**")

            if q['multi_select']:
                selected = st.multiselect("Select your answers:", q['options'], key=f"answer_{idx}")
            else:
                selected = st.radio("Select your answer:", q['options'], key=f"answer_{idx}")

            flag = st.checkbox("🚩 Flag this question", key=f"flag_{idx}")

            user_answers[str(idx)] = selected
            flags[str(idx)] = flag

        if st.button("Submit Test ✅"):
            records = []
            correct_count = 0
            for idx, answer in user_answers.items():
                correct = correct_answers.get(idx, [])
                if isinstance(answer, list):
                    selected_letters = [extract_option_letter(a) for a in answer]
                    selected_options = ", ".join(selected_letters)
                    correct_match = set(a.upper() for a in selected_letters) == set(c.upper() for c in correct)
                else:
                    selected_letter = extract_option_letter(answer)
                    selected_options = selected_letter
                    correct_match = set([selected_letter.upper()]) == set(c.upper() for c in correct)

                result = "Correct" if correct_match else "Incorrect"
                if result == "Correct":
                    correct_count += 1
                correct_ans_text = ", ".join(correct)

                records.append({
                    "Question Number": idx,
                    "Your Answer(s)": selected_options,
                    "Correct Answer(s)": correct_ans_text,
                    "Result": result,
                    "Flagged": "FLAGGED" if flags.get(idx) else ""
                })

            df = pd.DataFrame(records)

            output_filename = test_selected.replace(".md", ".xlsx")
            df.to_excel(output_filename, index=False)

            # Highlight incorrect answers
            wb = load_workbook(output_filename)
            ws = wb.active
            red_fill = PatternFill(start_color="FFFF0000", end_color="FFFF0000", fill_type="solid")

            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
                if row[3].value == "Incorrect":
                    for cell in row:
                        cell.fill = red_fill

            wb.save(output_filename)

            total_questions = len(questions)
            score_percentage = (correct_count / total_questions) * 100
            st.success(f"You scored {correct_count} out of {total_questions} ({score_percentage:.2f}%) 🎯")

            with open(output_filename, "rb") as f:
                st.download_button("Download your graded Excel file 📄", data=f, file_name=output_filename)

# ---------- Run App ----------

if __name__ == "__main__":
    main()
