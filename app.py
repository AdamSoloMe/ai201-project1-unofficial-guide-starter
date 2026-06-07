"""
Queens College CS Professor Unofficial Guide — Gradio web interface.

Run:
    python app.py
Then open http://localhost:7860
"""

import gradio as gr
from query import ask

EXAMPLE_QUESTIONS = [
    "Which CS professor at Queens College is the most highly rated?",
    "What do students say about Alex Ryba?",
    "Is Jerry Waxman a good professor?",
    "Which Queens College CS professor is the easiest?",
    "What do students complain about most in Queens College CS courses?",
    "Is Simina Fluture a hard professor?",
    "Which professor would students take again?",
    "What do students say about Jackson Yeh?",
]


def handle_query(question: str):
    if not question.strip():
        return "Please enter a question.", "", ""

    try:
        result = ask(question)
    except ValueError as e:
        return str(e), "", ""
    except Exception as e:
        return f"Error: {e}", "", ""

    answer = result["answer"]
    sources = "\n".join(f"• {s}" for s in result["sources"])

    chunk_lines = []
    for i, chunk in enumerate(result["chunks"], 1):
        chunk_lines.append(
            f"[{i}] {chunk['source']} (distance: {chunk['distance']})\n"
            f"{chunk['text'][:300]}{'…' if len(chunk['text']) > 300 else ''}"
        )
    retrieved = "\n\n".join(chunk_lines)

    return answer, sources, retrieved


with gr.Blocks(title="Queens College CS Professor Unofficial Guide") as demo:
    gr.Markdown(
        "# Queens College CS Professor Unofficial Guide\n"
        "Ask questions about CUNY Queens College Computer Science professors based on real "
        "Rate My Professors reviews. All answers are grounded in student reviews — sources are always cited."
    )

    with gr.Row():
        with gr.Column(scale=2):
            question_box = gr.Textbox(
                label="Your question",
                placeholder="e.g. Is Alex Ryba a good professor?",
                lines=2,
            )
            ask_btn = gr.Button("Ask", variant="primary")

            answer_box = gr.Textbox(
                label="Answer",
                lines=10,
                interactive=False,
            )
            sources_box = gr.Textbox(
                label="Sources",
                lines=3,
                interactive=False,
            )

        with gr.Column(scale=1):
            retrieved_box = gr.Textbox(
                label="Retrieved chunks (debug)",
                lines=20,
                interactive=False,
            )

    gr.Examples(
        examples=EXAMPLE_QUESTIONS,
        inputs=question_box,
        label="Example questions",
    )

    ask_btn.click(
        handle_query,
        inputs=question_box,
        outputs=[answer_box, sources_box, retrieved_box],
    )
    question_box.submit(
        handle_query,
        inputs=question_box,
        outputs=[answer_box, sources_box, retrieved_box],
    )

if __name__ == "__main__":
    demo.launch()
