# A‑S‑K — A Semantic Kernel (ASK)

A‑S‑K is a practical, testable framework and implementation blueprint for building AI systems that route, verify, and synthesize meaning. It treats language as a layered, compiler‑like stack from glyph geometry to discourse, enabling more transparent research workflows, richer annotations, and graph‑grounded reasoning.

This README is a standalone synthesis of the core concepts and the MVP path toward an AI‑powered research tool informed by A Semantic Kernel.


## Why A‑S‑K

- Structure first: Model language as layered computation rather than surface tokens alone.
- Trust by design: Bind every claim to provenance, typed structure, and uncertainty.
- Human‑AI collaboration: Keep humans in the loop for adjudication at decision boundaries.
- Scalability: Factor representations (operators vs payloads) to compress parameters while improving retrieval and analogy.


## A Semantic Kernel (ASK) — Core Model

ASK proposes a four‑layer stack. Each layer constrains the next and is optimized like a compiler pipeline:

1) Geometric Substrate (pre‑linguistic)
- Glyph affordances derived from simple forms: | stroke (distinction), O loop (enclosure), V aperture (receptivity), T cross (orthogonality/instantiation).
- These are biases, not hard meanings; they make certain encodings natural.

2) Glyph Operators (sub‑lexical)
- Consonants → operations (fold, turn, tighten, flow, route).
- Vowels → typed payloads (a base/open; e relational; i minimal/index; o whole/container; u rooted/enduring).
- Diphthongs → small structs (e.g., ae ≈ bound duality; ou ≈ enclosure/mapping; ui ≈ id–value unit).

3) Morphemes & Words (composition)
- Roots ≈ base functions; prefixes/suffixes ≈ decorators/coercions; inflections ≈ explicit pointers (tense/case/number).
- Latin is unusually transparent here, serving as a semantic routing case study.

4) Pragmatic Field (intent & effect)
- Speech‑act, audience model, context, and cultural priors govern routing choices and evaluation of effect.


## Latin as a Semantic Compiler (Analogy)

- Roots = primitive functions (manu‑ hand/handling; vert‑ turn; plic‑ fold).
- Prefixes/suffixes = wrappers/coercions (trans‑, meta‑, ‑tion, ‑itas).
- Inflectional endings = explicit pointers (tense/case/number).
- Treat consonant clusters as operators (mn handle; vr turn; pl/plic fold) and vowels as typed payloads.

Examples (tendencies, not rules):
- mn/man‑ → grasp/handle (manus, manipulate)
- pl/plic‑ → fold/layer/multiply (apply, multiply)
- vr/vert‑ → turn/route (invert, convert)


## A Calculus of Information–Causality

A working formula for how symbols produce effects:

E = k × A × M

- E (Effect): magnitude of impact in a target substrate (mind, org, system).
- k (Causality Constant): responsiveness of the substrate (openness, channel, modality).
- A (Alignment): structural resonance between symbol and target (feature overlap, schema fit).
- M (Meaning Density): coherent, orthogonal dimensions encoded; grows superlinearly with structure.

Practical use: increase A by mirroring target schemas; increase M by layering orthogonal evidence/features without redundancy.


## Reference Architecture (Semantic Routing Engine)

1) Capture: ingest web/text with provenance, timestamps, and hashing.
2) Lex–Morph Analyzer: segment prefixes/roots/suffixes/inflections; tag operator vs payload features.
3) Operator–Payload Factorizer: produce typed embeddings separating consonant operations from vowel payloads.
4) Semantic Composer: apply decorators/coercions; emit typed AST‑like structures per utterance.
5) Graph Binder: ground nodes/edges to an ontology with confidence and justifications.
6) Verifier: retrieval + counterfactual checks; highlight disagreements for human review.
7) Router: traverse operator paths for analogy and retrieval (e.g., fold‑family, turn→convert paths).
8) UX: accordion rationales, inline provenance, diff views for claims vs sources.


### Minimal Data Sketch

```json
{
  "Token": {
    "surface": "manipulation",
    "morph": { "prefix": null, "root": "man", "theme": "-ipul-", "suffix": "-ation" },
    "operators": ["mn", "pl"],
    "payloads": ["a", "i", "u", "o"],
    "features": { "action": "handle→fold→result", "type": "process→noun" }
  },
  "GraphNode": {
    "id": "Q123",
    "label": "Handling-With-Folding",
    "type": "Process",
    "evidence": ["doi:10.1234/abcd"],
    "confidence": 0.82,
    "facets": { "operatorPath": ["mn","pl"], "payloadSchema": {"a":"index→u:o"} }
  }
}
```


## MVP for the AI Research & Annotation Tool

Phase 1 (6–8 weeks)
- Web capture with highlights→claims extraction; source hashing.
- Morphological tagging for English/Latin; inline chips for operators/payloads with confidence.
- Claim graph with provenance; reviewer workflow (accept/reject, notes, audit trail).

Phase 2 (6–10 weeks)
- Train operator–payload embeddings; evaluate on analogy and sense disambiguation.
- Add routing queries (e.g., “fold‑family analogs of X”).
- Instrument dashboard to track predictions/hypotheses (below).

Phase 3
- Team spaces, role‑based gates, ontology alignment, and API for external agents with rationale constraints.

Key KPIs and Guardrails
- Time‑to‑verified‑claim; reviewer agreement; retrieval precision; rationale coverage.
- Provenance mandatory; uncertainty tracked; reversible merges and diffs.


## Test Bench: Common Word Decodings

Operationalize the framework on high‑frequency words to validate utility and tune priors. A record looks like:

```json
{
  "word": "give",
  "category": "verb",
  "operators": ["g", "v"],
  "payloads": ["i", "e"],
  "gloss": "impulse along a channel → transfer",
  "provenance": "PIE *gʰebʰ- (to give)",
  "confidence": "H"
}
```

Patterns to watch
- Modal -ould: ou (enclosure/mapping) + ld (hold/fold) with initial operator setting mode (w will; c/capacity; sh/ought).
- str‑ cluster: structure/constraint/tighten (string, strong, strict).
- gh: historical aspiration/clarity or force (light, might, sight, fight).


## Falsifiable Predictions (for empirical grounding)

1) Cursive Angularity Hypothesis: pen angles/lifts correlate with semantic orthogonality across linked words.
2) Capitalization Energy‑Barrier: capitals require measurably more effort, tracking conceptual primacy.
3) T‑Density Hypothesis: glyph “T” frequency correlates with structural/abstract reasoning demands.

Additional tests: cross‑lingual operator invariants; vowel‑type priors in disambiguation; graph compression from factorization vs baseline LMs.


## Limits, Caveats, Ethics

- Generative model, not universal etymology; treat phonosemantics as priors, not proof.
- Use morphology and provenance before phonetic intuition when in conflict.
- Respect language diversity; avoid Indo‑European bias where it does not fit.
- Expose alignment and meaning‑density overlays to reduce manipulative rhetoric.


## Roadmap (selected)

- Operator–payload embeddings with ablation studies (operators‑only vs payloads‑only vs combined).
- Knowledge graph schema evolution and ontology alignment tools.
- Reviewer playbooks and inter‑annotator agreement metrics for function words.
- Cross‑family replication (Semitic root‑and‑pattern, Sinitic morphosyllabic, Uralic).


## Contributing

- Propose operator mappings or counterexamples with citations.
- Add decoded words with confidence ratings and provenance.
- Open issues for experimental design or UX flows that improve adjudication.


## License

This project is licensed under the MIT License. See [`LICENSE`](./LICENSE) for details.


## Install

Prerequisites: Python 3.10+

- Create a virtual environment and install in editable mode (recommended for development):

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

- Alternatively, just install dependencies without packaging (not recommended for CLI usage):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```


## Quickstart

- Decode a word using the unified CLI (enhanced by default):

```bash
ask decode ask
ask decode manipulation --json
```

- Seed data lives in `data/decoded_words.jsonl` as JSONL records for the Test Bench.


## CLI Usage

All commands assume the package is installed (e.g., `python3 -m pip install -e .`).

### ask (unified CLI)

```bash
# Help and available commands
ask --help

# Decode a single word (enhanced view)
ask decode ask

# Minimal view (no morphology block or details)
ask decode manipulation --simple

# JSON output for scripting
ask decode manipulation --json

# Verbose analysis with operator principles and payload types
ask decode manipulation --verbose

# Audit a decoded word with OpenAI (requires OPENAI_API_KEY)
OPENAI_API_KEY=sk-... ask audit "ask" --model gpt-5-mini

# Extract article content (requires FIRECRAWL_API_KEY)
FIRECRAWL_API_KEY=fc-... ask extract https://example.com/article

# Batch extract from a file of URLs (one per line)
FIRECRAWL_API_KEY=fc-... ask extract-batch --file urls.txt > results.json

# List operators or clusters with confidence
ask operators
ask clusters

# Validate the ASK kernel proof and run self-tests
ask validate

# Batch decode
ask batch "ask,think,understand,manipulation" --json
```

### ask-fields (field-based glyph analysis CLI)

```bash
# Help
ask-fields --help

# Decode with field-based operators and confidence tracking
ask-fields decode manipulation --detailed

# Inspect a glyph's field
ask-fields field k

# System statistics and high-confidence associations
ask-fields stats

# Teach the system a correct association (adjust confidence)
ask-fields learn "manipulation" p present --confidence 0.1

# Batch decode words from a file
ask-fields batch-decode words.txt --output results.json
```

## Environment

Create a `.env` file at the project root with any provider keys you want to use (optional):

```env
OPENAI_API_KEY=...  # required for audit command
# HUGGINGFACE_API_KEY=...
# GEMINI_API_KEY=...
```

Note: `.env` is listed in `.gitignore`. Do not commit secrets.


## Audit (Model-assisted review)

Use OpenAI `gpt-5-mini` to audit a decoded word (requires `OPENAI_API_KEY` in environment):

```bash
PYTHONPATH=src OPENAI_API_KEY=your_key python -m ask.cli audit ask
```

Options:

- `--model` to select an OpenAI chat model (default `gpt-5-mini`).
- `--no-json-out` to print a pretty (non-JSON) report.


## Project Structure

```
A-S-K/
├── README.md           # This file: overview and synthesis
├── GLYPHS.md           # The Standard Model of Glyphic Axioms
├── LICENSE             # MIT license
├── CONTRIBUTING.md     # How to contribute, dev setup
├── requirements.txt    # Runtime deps (typer, pydantic, rich)
├── examples/           # Notebooks and runnable scripts
├── data/               # Decoded word corpus and test sets
│   └── decoded_words.jsonl
├── tests/              # Unit tests (pytest)
└── src/                # Implementation code
    └── ask/
        ├── __init__.py
        ├── glyphs.py          # Operator/payload maps and clusters
        ├── factorizer.py      # decode_word(), extraction helpers
        ├── compose.py         # Minimal AST-like composition
        └── cli.py             # Typer CLI (python -m ask.cli)
```


## The ASK Proof: Self-Evidence

The word "ask" itself demonstrates the framework:

- **A** (aperture): Opens a typed unknown "?"
- **S** (stream): Broadcasts the query outward
- **K** (clamp): Resolves responses to discrete answer

Thus "ask" literally encodes the semantic kernel operation: instantiate unknown → route request → resolve result. This is why we've named the project A-S-K.


---

*For the complete glyph-level axioms and geometric complementarity patterns, see [GLYPHS.md](./GLYPHS.md)*
