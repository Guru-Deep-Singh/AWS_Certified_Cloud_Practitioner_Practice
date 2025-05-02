import streamlit as st
import pandas as pd
import re
import os
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

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

        multi_select = bool(re.search(r'\((Choose|Select) (TWO|THREE|FOUR)\)', q_text, re.IGNORECASE))

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

def main():
    st.title("📚 Take Your MCQ Test with Grading!")

    uploaded_file = st.file_uploader("Upload your questions .md file", type=["md"], key="questions")
    uploaded_answers = st.file_uploader("Upload your answers .md file", type=["md"], key="answers")

    if uploaded_file and uploaded_answers:
        md_path = os.path.join("temp_questions.md")
        with open(md_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        ans_path = os.path.join("temp_answers.md")
        with open(ans_path, "wb") as f:
            f.write(uploaded_answers.getbuffer())

        questions = parse_md_file(md_path)
        correct_answers = parse_answers_file(ans_path)

        st.success(f"Parsed {len(questions)} questions!")

        user_answers = {}
        flags = {}

        for idx, q in enumerate(questions, 1):
            st.markdown(f"**{idx}. {q['question']}**")

            if q['multi_select']:
                selected = st.multiselect(f"Select your answers:", q['options'], key=f"answer_{idx}")
            else:
                selected = st.radio(f"Select your answer:", q['options'], key=f"answer_{idx}")

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
                    correct_match = set(selected_letters) == set(c.strip() for c in correct)
                else:
                    selected_letter = extract_option_letter(answer)
                    selected_options = selected_letter
                    correct_match = set([selected_letter]) == set(c.strip() for c in correct)

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
            output_path = "your_answers_with_grades.xlsx"
            df.to_excel(output_path, index=False)

            # Highlight incorrect answers in red
            wb = load_workbook(output_path)
            ws = wb.active
            red_fill = PatternFill(start_color="FFFF0000", end_color="FFFF0000", fill_type="solid")

            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
                result_cell = row[3]  # "Result" column is 4th (index 3)
                if result_cell.value == "Incorrect":
                    for cell in row:
                        cell.fill = red_fill

            wb.save(output_path)

            total_questions = len(questions)
            score_percentage = (correct_count / total_questions) * 100
            st.success(f"You scored {correct_count} out of {total_questions} ({score_percentage:.2f}%) 🎯")

            with open(output_path, "rb") as f:
                st.download_button("Download your graded Excel file 📄", data=f, file_name="your_answers_with_grades.xlsx")

if __name__ == "__main__":
    main()
