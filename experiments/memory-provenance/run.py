#!/usr/bin/env python3
"""Reproduce the synthetic retrieval experiment and its three SVG figures."""

import csv
import hashlib
import io
import json
import math
import re
import textwrap
from collections import Counter
from datetime import date
from html import escape
from pathlib import Path
from xml.etree import ElementTree


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FIGURES = ROOT / "images" / "memory"
BUDGETS = (1, 2, 4, 8)
CATEGORIES = ("eligible", "superseded", "wrong_subject", "out_of_scope", "prohibited")
LABELS = {
    "eligible": "Eligible",
    "superseded": "Superseded",
    "wrong_subject": "Wrong subject",
    "out_of_scope": "Out of scope",
    "prohibited": "Prohibited",
}
COLORS = {
    "eligible": "#147d73",
    "superseded": "#94620b",
    "wrong_subject": "#6b60a8",
    "out_of_scope": "#60758b",
    "prohibited": "#bd4655",
}
STOP = set(
    "a an and are as at be but by can for from i in is it me my of on or "
    "please that the this to we when where with you".split()
)


def tokens(text):
    return [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOP]


def validate(data):
    memories = data["conversations"]
    queries = data["queries"]
    ids = {memory["id"] for memory in memories}
    if len(ids) != len(memories):
        raise ValueError("Duplicate memory ID")
    if len({query["id"] for query in queries}) != len(queries):
        raise ValueError("Duplicate query ID")
    by_id = {memory["id"]: memory for memory in memories}
    for memory in memories:
        date.fromisoformat(memory["date"])
        if not memory["source"].strip() or not memory["claim"].strip():
            raise ValueError("Empty source or claim: " + memory["id"])
        if not isinstance(memory["reusable"], bool):
            raise ValueError("Reuse permission must be boolean")
        if "superseded_by" in memory:
            replacement = by_id[memory["superseded_by"]]
            if replacement["date"] <= memory["date"]:
                raise ValueError("Replacement must be newer")
    for query in queries:
        date.fromisoformat(query["date"])
        if set(query["gold"]) != set(CATEGORIES):
            raise ValueError("Missing or unexpected gold categories: " + query["id"])
        assigned = [item for category in CATEGORIES for item in query["gold"][category]]
        if len(assigned) != len(set(assigned)) or set(assigned) != ids:
            raise ValueError("Gold labels must partition all cues: " + query["id"])


def rank(memories, query):
    """TF-IDF cosine over source text; positive scores only; ID breaks ties."""
    available = [memory for memory in memories if memory["date"] <= query["date"]]
    documents = [Counter(tokens(memory["source"])) for memory in available]
    frequency = Counter(word for document in documents for word in document)
    idf = {
        word: math.log((1 + len(documents)) / (1 + count)) + 1
        for word, count in frequency.items()
    }

    def vector(counts):
        weighted = {word: count * idf[word] for word, count in counts.items() if word in idf}
        norm = math.sqrt(sum(value * value for value in weighted.values()))
        return {word: value / norm for word, value in weighted.items()} if norm else {}

    query_vector = vector(Counter(tokens(query["text"])))
    scores = []
    for memory, document in zip(available, documents):
        document_vector = vector(document)
        score = sum(value * document_vector.get(word, 0) for word, value in query_vector.items())
        if score > 0:
            scores.append((memory["id"], score))
    return sorted(scores, key=lambda item: (-item[1], item[0]))


def permitted(memory, query, by_id):
    """Hand-authored metadata control; never reads query gold labels."""
    replacement_id = memory.get("superseded_by")
    superseded = replacement_id is not None and by_id[replacement_id]["date"] <= query["date"]
    return (
        memory["date"] <= query["date"]
        and memory["reusable"]
        and not superseded
        and memory["subject"] in query["subjects"]
        and bool(set(memory["topics"]) & set(query["topics"]))
        and memory["scope"] in ("global", query["scope"])
    )


def evaluate(data):
    validate(data)
    by_id = {memory["id"]: memory for memory in data["conversations"]}
    details = []
    summary = []
    for method in ("lexical", "metadata_control"):
        for budget in BUDGETS:
            counts = Counter({category: 0 for category in CATEGORIES})
            selected_total = eligible_total = nonuse_correct = nonuse_total = 0
            for query in data["queries"]:
                ranked = rank(data["conversations"], query)
                if method == "metadata_control":
                    ranked = [
                        pair for pair in ranked if permitted(by_id[pair[0]], query, by_id)
                    ]
                selected = ranked[:budget]
                gold = query["gold"]
                eligible_total += len(gold["eligible"])
                if not gold["eligible"]:
                    nonuse_total += 1
                    nonuse_correct += int(not selected)
                for position, (memory_id, score) in enumerate(selected, 1):
                    category = next(key for key in CATEGORIES if memory_id in gold[key])
                    counts[category] += 1
                    selected_total += 1
                    details.append({
                        "method": method, "budget": budget, "query": query["id"],
                        "rank": position, "memory": memory_id,
                        "score": round(score, 9), "category": category,
                    })
            summary.append({
                "method": method, "budget": budget, "queries": len(data["queries"]),
                "selected": selected_total, **dict(counts),
                "eligible_total": eligible_total,
                "precision": counts["eligible"] / selected_total if selected_total else None,
                "recall": counts["eligible"] / eligible_total if eligible_total else None,
                "correct_nonuse": nonuse_correct, "nonuse_queries": nonuse_total,
            })
    return details, summary


class SVG:
    def __init__(self, height, title, description):
        self.height = height
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" '
            f'viewBox="0 0 1200 {height}" style="max-width:100%;height:auto" '
            f'role="img" aria-labelledby="title description">',
            f"<title id=\"title\">{escape(title)}</title>",
            f"<desc id=\"description\">{escape(description)}</desc>",
            '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#172b44}'
            '.small{font-size:17px}.body{font-size:21px}.heading{font-size:26px;font-weight:700}'
            '.title{font-size:37px;font-weight:700}.muted{fill:#52657b}</style>',
            '<rect width="1200" height="100%" fill="#f5f7fb"/>',
        ]
        self.text(48, 47, "SYNTHETIC CASE STUDY  /  MEMORY & PROVENANCE", "small muted")
        self.text(48, 101, title, "title")

    def text(self, x, y, value, css="body", fill=None, anchor=None):
        extra = (f' style="fill:{fill}"' if fill else "")
        extra += (f' text-anchor="{anchor}"' if anchor else "")
        self.parts.append(
            f'<text x="{x}" y="{y}" class="{css}"{extra}>{escape(str(value))}</text>'
        )

    def wrapped(self, x, y, value, width=42, css="body", step=28):
        for index, line in enumerate(textwrap.wrap(value, width)):
            self.text(x, y + index * step, line, css)

    def box(self, x, y, width, height, fill="#ffffff", stroke="#dae2ed"):
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
            f'rx="12" fill="{fill}" stroke="{stroke}"/>'
        )

    def line(self, x1, y1, x2, y2, color="#a6b4c6"):
        self.parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2"/>'
        )

    def save(self, path):
        path.write_text("\n".join(self.parts + ["</svg>", ""]), encoding="utf-8")


def timeline(data):
    by_id = {memory["id"]: memory for memory in data["conversations"]}
    svg = SVG(
        870, "Remembered correctly. Used incorrectly.",
        "Four fictional conversation cues evaluated against a solo restaurant request: "
        "use the June update, not the superseded January diet, father's access needs, "
        "or a task-local abstract limit. This diagram is illustrative, not model output.",
    )
    svg.text(48, 144, "One current request: Find a restaurant for my solo trip.", "body muted")
    rows = [
        ("m01", "JAN", "superseded", "Later dietary update replaces this cue."),
        ("m03", "MAR", "wrong_subject", "The statement is about the father."),
        ("m06", "JUN", "eligible", "Current dietary cue for this user."),
        ("m09", "SEP", "out_of_scope", "A limit for one abstract, not this task."),
    ]
    svg.line(92, 207, 92, 710)
    for index, (memory_id, month, category, explanation) in enumerate(rows):
        y = 185 + index * 140
        memory = by_id[memory_id]
        svg.box(48, y + 22, 88, 52, "#e7edf5")
        svg.text(92, y + 55, month, "body", anchor="middle")
        svg.box(161, y, 605, 119)
        svg.text(183, y + 31, f"{memory_id}  /  source conversation", "small muted")
        svg.wrapped(183, y + 64, memory["source"], width=52, css="body", step=25)
        svg.box(787, y, 365, 119)
        svg.text(809, y + 34, LABELS[category].upper(), "body", fill=COLORS[category])
        svg.wrapped(809, y + 66, explanation, width=31, css="small", step=23)
    svg.box(48, 766, 1104, 63, "#e3f1ed", "#b6d8cf")
    svg.text(70, 805, "Accurate recall does not establish appropriate reuse.", "heading")
    svg.save(FIGURES / "01_memory_timeline.svg")


def retrieval_figure(summary):
    import seaborn as sns
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from matplotlib.patches import Patch

    max_count = max(row["selected"] for row in summary)
    axis_max = max(10, math.ceil(max_count / 10) * 10)
    theme = {
        "axes.facecolor": "#f5f7fb", "figure.facecolor": "#f5f7fb",
        "text.color": "#172b44", "axes.labelcolor": "#172b44",
        "xtick.color": "#52657b", "ytick.color": "#52657b",
        "grid.color": "#dce3ed", "font.family": "sans-serif",
    }
    with sns.axes_style("whitegrid", rc=theme), sns.plotting_context("notebook"):
        figure = Figure(figsize=(12, 9.5))
        FigureCanvasAgg(figure)
        axes = figure.subplots(1, 2)
        figure.subplots_adjust(left=0.085, right=0.97, bottom=0.23, top=0.66, wspace=0.18)
        figure.text(0.06, 0.95, "SYNTHETIC CASE STUDY / MEMORY & PROVENANCE",
                    fontsize=11, color="#52657b")
        figure.text(0.06, 0.89, "What changes when retrieval gets bigger?",
                    fontsize=24, weight="bold")
        figure.text(0.06, 0.845,
                    "Selected cue-request pairs across 8 requests; up to k positive-score cues per request.",
                    fontsize=11, color="#52657b")
        figure.legend(
            handles=[Patch(facecolor=COLORS[key], label=LABELS[key]) for key in CATEGORIES],
            loc="upper left", bbox_to_anchor=(0.06, 0.815), ncol=3, frameon=False,
        )
        for panel, method in enumerate(("lexical", "metadata_control")):
            ax = axes[panel]
            rows = sorted(
                (row for row in summary if row["method"] == method),
                key=lambda row: row["budget"],
            )
            points = [
                (index, row[category], category)
                for index, row in enumerate(rows) for category in CATEGORIES
            ]
            sns.histplot(
                data={
                    "budget_position": [point[0] for point in points],
                    "count": [point[1] for point in points],
                    "category": [point[2] for point in points],
                },
                x="budget_position", weights="count", hue="category",
                hue_order=list(reversed(CATEGORIES)), palette=COLORS,
                bins=[index - 0.5 for index in range(len(rows) + 1)],
                multiple="stack", stat="count", common_norm=False,
                shrink=0.66, alpha=1, edgecolor="#f5f7fb", linewidth=0.5,
                legend=False, ax=ax,
            )
            for bar in ax.patches:
                if bar.get_height() >= 3:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_y() + bar.get_height() / 2,
                        f"{bar.get_height():.0f}", ha="center", va="center",
                        fontsize=11, color="white",
                    )
            tick_labels = []
            for index, row in enumerate(rows):
                precision = "-" if row["precision"] is None else f"{row['precision']:.1%}"
                tick_labels.append(f"k={row['budget']}\n{precision}")
                ax.text(index, row["selected"] + 0.65, str(row["selected"]),
                        ha="center", fontsize=12, weight="bold")
            ax.set(
                xticks=list(range(len(rows))), xticklabels=tick_labels,
                xlim=(-0.6, len(rows) - 0.4), ylim=(0, axis_max),
                yticks=list(range(0, axis_max + 1, 10)),
                xlabel="Retrieval budget k\nPercent below k = eligible / selected",
                ylabel="Selected cue-request pairs" if panel == 0 else "",
            )
            ax.set_title(
                "Lexical relevance only" if panel == 0 else "Hand-annotated metadata control",
                loc="left", fontsize=13, weight="bold", pad=36,
            )
            ax.text(
                0, 1.035,
                "No subject, time, or reuse checks" if panel == 0 else
                "Same ranking; filter before taking top k",
                transform=ax.transAxes, fontsize=10, color="#52657b",
            )
            ax.grid(axis="x", visible=False)
            sns.despine(ax=ax, left=True, bottom=True)
        figure.text(0.06, 0.10, "A control, not a learned capability",
                    fontsize=14, weight="bold")
        figure.text(0.06, 0.065,
                    "Subject, topic, scope, updates, and permissions are supplied by hand. No LLM is run.",
                    fontsize=11, color="#52657b")
    return figure


def retrieval_chart(summary):
    import matplotlib as mpl

    with mpl.rc_context({"svg.fonttype": "none", "svg.hashsalt": "memory-provenance"}):
        figure = retrieval_figure(summary)
        buffer = io.BytesIO()
        figure.savefig(buffer, format="svg", metadata={"Date": None, "Creator": "Seaborn / Matplotlib"})
        figure.clear()
    namespace = "http://www.w3.org/2000/svg"
    ElementTree.register_namespace("", namespace)
    root = ElementTree.fromstring(buffer.getvalue())
    root.set("role", "img")
    root.set("aria-labelledby", "title description")
    root.set("style", "max-width:100%;height:auto")
    title = ElementTree.Element(f"{{{namespace}}}title", id="title")
    title.text = "What changes when retrieval gets bigger?"
    description = ElementTree.Element(f"{{{namespace}}}desc", id="description")
    description.text = (
        "Seaborn stacked histograms of measured cue-request counts across eight synthetic requests "
        "at budgets 1, 2, 4, and 8. Lexical retrieval selects 8, 15, 24, and 36 pairs; "
        "7, 8, 10, and 11 are eligible. The hand-annotated metadata control selects "
        "7, 10, 13, and 13 pairs, all eligible. These are not LLM performance results."
    )
    root.insert(0, title)
    root.insert(1, description)
    ElementTree.ElementTree(root).write(
        FIGURES / "02_retrieval_budget.svg", encoding="utf-8", xml_declaration=True,
    )


def provenance():
    svg = SVG(
        820, "A source link is not enough.",
        "Illustrative provenance failure: a statement that the father needs step-free access "
        "is transformed into a user profile claim. A corrected branch preserves the subject "
        "and excludes the cue from a solo trip. No model generated these transformations.",
    )
    svg.text(48, 144, "Same source. Two transformations. Different conclusions.", "body muted")
    svg.box(240, 178, 720, 105)
    svg.text(266, 213, "SOURCE m03  /  March conversation", "small muted")
    svg.wrapped(266, 248, "My father needs step-free access when we visit a restaurant or hotel.", width=61)
    svg.line(600, 283, 600, 310)
    svg.line(305, 310, 895, 310)
    svg.line(305, 310, 305, 342)
    svg.line(895, 310, 895, 342)
    svg.box(48, 342, 514, 125, "#fbebee", "#e7b6be")
    svg.text(72, 378, "SUBJECT LOST", "heading", fill=COLORS["prohibited"])
    svg.wrapped(72, 416, "Profile: User needs step-free access.", width=38)
    svg.box(638, 342, 514, 125, "#e3f1ed", "#b6d8cf")
    svg.text(662, 378, "SUBJECT PRESERVED", "heading", fill=COLORS["eligible"])
    svg.wrapped(662, 416, "Memory: Father needs step-free access.", width=38)
    svg.line(305, 467, 305, 505)
    svg.line(895, 467, 895, 505)
    svg.box(48, 505, 514, 145)
    svg.text(72, 542, "Solo-trip answer cites m03", "body")
    svg.wrapped(72, 580, "The citation exists, but it does not support a claim about the user.", width=41)
    svg.box(638, 505, 514, 145)
    svg.text(662, 542, "Solo-trip answer excludes m03", "body")
    svg.wrapped(662, 580, "The source remains traceable without becoming a user preference.", width=41)
    svg.box(48, 697, 1104, 80)
    svg.text(70, 731, "Check claim support, not merely whether a citation is present.", "heading")
    svg.text(70, 759, "Illustrative transformation, not measured LLM behavior or proof of causal influence.", "small muted")
    svg.save(FIGURES / "03_provenance_branches.svg")


def main():
    source = HERE / "case_study.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    details, summary = evaluate(data)
    output = HERE / "results"
    output.mkdir(exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps({
        "dataset_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "method": "TF-IDF cosine over source spans; positive scores only; stable ID tie-break.",
        "annotation": "Hand-authored gold labels and metadata; not learned or model-extracted.",
        "rows": summary,
    }, indent=2) + "\n", encoding="utf-8")
    with (output / "selections.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, lineterminator="\n", fieldnames=[
            "method", "budget", "query", "rank", "memory", "score", "category",
        ])
        writer.writeheader()
        writer.writerows(details)
    timeline(data)
    retrieval_chart(summary)
    provenance()
    print("method             k  selected eligible precision recall non-use")
    for row in summary:
        precision = "-" if row["precision"] is None else f"{row['precision']:.1%}"
        print(f"{row['method']:18} {row['budget']}  {row['selected']:8} "
              f"{row['eligible']:8} {precision:>9} {row['recall']:6.1%} "
              f"{row['correct_nonuse']}/{row['nonuse_queries']}")
    print("Wrote results/summary.json, results/selections.csv, and three SVG figures.")


if __name__ == "__main__":
    main()
