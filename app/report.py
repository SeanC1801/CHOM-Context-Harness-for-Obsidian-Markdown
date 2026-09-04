from fpdf import FPDF

def build_report_data(conn, session_id: str) -> dict:
    session_row = conn.execute(
        "SELECT proposal, first_question FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()

    answer_rows = conn.execute(
        "SELECT question, answer FROM answers WHERE session_id = ? ORDER BY created_at",
        (session_id,),
    ).fetchall()

    comparison_rows = conn.execute(
        """
        SELECT option_scores.option_name AS option_name,
               SUM(option_scores.score * criteria.weight) AS total_score
        FROM option_scores
        JOIN criteria ON criteria.id = option_scores.criterion_id
        WHERE option_scores.session_id = ?
        GROUP BY option_scores.option_name
        ORDER BY total_score DESC
        """,
        (session_id,),
    ).fetchall()

    return {
        "proposal": session_row["proposal"],
        "answers": [{"question": row["question"], "answer": row["answer"]} for row in answer_rows],
        "options": [{"name": row["option_name"], "total_score": row["total_score"]} for row in comparison_rows],
    }

def render_markdown(data: dict) -> str:
    lines = ["# CHOM Project Brief", "", "## Proposal", "", data["proposal"], ""]

    lines.append("## Questions and Answers")
    lines.append("")
    for item in data["answers"]:
        lines.append(f"**Q: {item['question']}**")
        lines.append(f"A: {item['answer']}")
        lines.append("")

    lines.append("## Option Comparison")
    lines.append("")
    for option in data["options"]:
        lines.append(f"- **{option['name']}** — total score: {option['total_score']}")

    return "\n".join(lines)

def render_pdf(data: dict, output_path: str) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    pdf.cell(0, 10, "CHOM Project Brief", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, _sanitize_for_pdf(f"Proposal:\n{data['proposal']}"))
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Questions and Answers", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=12)
    for item in data["answers"]:
        pdf.multi_cell(0, 8, _sanitize_for_pdf(f"Q: {item['question']}\nA: {item['answer']}"))
        pdf.ln(2)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Option Comparison", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=12)
    for option in data["options"]:
        pdf.cell(0, 8, _sanitize_for_pdf(f"{option['name']} - total score: {option['total_score']}"), new_x="LMARGIN", new_y="NEXT")

    pdf.output(output_path)

def _sanitize_for_pdf(text: str) -> str:
    replacements = {
        "\u2014": "-",   # em dash
        "\u2013": "-",   # en dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2026": "...", # ellipsis
    }
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)  
    return text.encode("latin-1", "replace").decode("latin-1")