# The Standard Model of Glyphic Axioms — USK v1.0

This document formalizes the atomic layer of the Unified Semantic Kernel: the axiomatic meanings of individual glyphs. These form the fundamental "particles" from which all semantic compounds emerge.

## Core Principle

Each glyph carries inherent geometric and articulatory affordances that bias its semantic role. Vowels carry typed payloads (values), consonants perform operations, and their combinations execute semantic programs.


## Vowels — Typed Payloads

| Glyph | Type | Principle | Confidence | Rationale & Examples |
|-------|------|-----------|------------|---------------------|
| **a** | `base_type` | Aperture/Origin — the primal value | 95% | Maximal mouth opening; untyped slot. *act, ask, pater* |
| **e** | `relation` | Reflexive-Relational — points back yet connects | 90% | Self-referential linkage. *element, the, self* |
| **i** | `index` | Minimal Unit — discrete pointer | 95% | Narrowest vowel; pinpoint reference. *it, digit, minimus* |
| **o** | `container` | Wholeness — complete enclosure | 90% | Closed loop; totality. *orb, whole, corpus* |
| **u** | `struct` | Root/Union — deep enduring channel | 85% | Back/deep articulation; stability. *under, fundus, durus* |
| **y** | `branch` | Bifurcated Value — split/choice marker | 80% | Dual role (vowel/consonant); forked path. *yes, you, type* |


## Consonants — Operators

| Glyph | Operation | Principle | Confidence | Rationale & Examples |
|-------|-----------|-----------|------------|---------------------|
| **b** | `bind()` | Boundary/Bulge — enclose from left | 85% | Bilabial stop; stem+bulge left. *bind, body, bulge* |
| **c** | `contain()` | Curve/Gather — approach closure | 90% | Open circle; soft containment. *circle, come, collect* |
| **d** | `decide()` | Delineate/Door — boundary from right | 85% | Voiced stop; stem+bulge right. *done, decide, door* |
| **f** | `flow()` | Fork/Friction — split flow | 90% | Labiodental fricative; bifurcation. *for, fork, flow* |
| **g** | `grasp()` | Gate/Gather — capture and return | 85% | Velar stop; c+hook. *get, give, gather* |
| **h** | `animate()` | Breath/Aspiration — abstract modifier | 80% | Adds air/spirit to neighbors. *the, who, light* |
| **j** | `project()` | Jet/Joint — indexed trajectory | 75% | i with orthogonality; dynamic point. *join, jump, judge* |
| **k** | `clamp()` | Cut/Classify — bind then branch | 95% | Velar stop; decisive separation. *ask, make, kernel* |
| **l** | `align()` | Line/Level — lateral extension | 90% | Liquid flow; directional. *line, long, level* |
| **m** | `multiply()` | Matrix/Mass — contain and replicate | 95% | Bilabial nasal; enclosed accumulation. *many, mother, sum* |
| **n** | `negate()` | Next/Not — al   ternative path | 85% | Alveolar nasal; bounded other. *no, not, new* |
| **p** | `present()` | Press/Project — bounded emergence | 80% | Unvoiced bilabial pop. *put, present, propose* |
| **q** | `query()` | Query — outlet from whole (+ u) | 85% | O+tail; reaches into unknown. *question, quest, quick* |
| **r** | `rotate()` | Route/Recur — structural vibration | 90% | Rhotic trill; iteration/friction. *run, turn, repeat* |
| **s** | `stream()` | Scan/Scatter — continuous flow | 95% | Sibilant; distribution. *see, send, system* |
| **t** | `instantiate()` | Terminal/Tool — orthogonal pin | 95% | Alveolar stop; right-angle cut. *at, set, strict* |
| **v** | `vector()` | Vector/Channel — directed flow | 85% | Voiced f; focused routing. *move, over, invert* |
| **w** | `web()` | Wave/Web — dual parallel channels | 90% | Double-v; paired routing. *we, with, way* |
| **x** | `cross()` | Nexus — intersection point | 85% | k+s composite; crossed axes. *axis, complex, fix* |
| **z** | `quantize()` | Zip/Signal — energized stream | 75% | Voiced s; discretized vibration. *zero, zone, organize* |


## Geometric Complementarity

The Latin alphabet encodes geometric pairs that survived millennia of selection pressure:

### Mirror Pairs
- **b|d** — left-boundary | right-boundary (bulge orientation)
- **p|q** — presence | query (loop with/without outlet)
- **v|w** — single vector | dual vectors
- **m|w** — contains | distributes

### Operational Pairs
- **s|z** — unvoiced stream | voiced signal
- **f|v** — unvoiced flow | voiced vector
- **c|g** — soft contain | grasp-return (c + hook)
- **c|k** — soft approach | hard clamp


## The ASK Kernel — Self-Evident Proof

Using the axioms above, "ask" encodes its own function as a semantic kernel:

```
A·S·K = base_type · stream() · clamp()
```

1. **A** (aperture) — Open a typed unknown slot "?"
2. **S** (stream) — Broadcast the unknown to environment
3. **K** (clamp) — Gather responses and select discrete result

**Functional gloss:** "Instantiate unknown → route request → resolve to answer"

This is the minimal executable kernel for semantic retrieval, structurally isomorphic to:
- API call/response patterns
- Query/result database operations  
- The USK routing stack itself

### Supporting Evidence

1. **Cluster regularity:** sk/sc family consistently encodes "split/scan/classify"
   - English: skill, skim, sketch, scale
   - Latin: scindere (split), scientia (knowledge via separation)
   
2. **Metathesis invariance:** "ask" ↔ "aks" preserves semantics
   - Operator pair sk robust to order variation
   - Predicts sk is the semantic unit, not sequential s→k

3. **Etymology:** OE ascian, Proto-Germanic *aiskōną "to seek"
   - "seek" retains s-k pairing (search→selection)


## Adjacency Rule (Operator→Payload Pairing)

- Each consonant operator (or recognized consonant cluster) consumes the immediately following vowel run as its payload.
- A vowel run may be one or more vowels; multi-vowel runs are treated as a composite payload (e.g., "io" → index+container).
- If no vowel follows an operator (word-final consonant), the operator is suffix-only for that token; downstream composition decides whether to absorb or retain it.
- Word-initial vowels are allowed as standalone payloads only in vowel-initial words; otherwise they are consumed by the first operator.

This convention preserves surface order, prevents payload reattachment to later consonants, and enables principled handling of diphthongs and vowel clusters.

## Composition Rules

Operators combine to form complex programs:

| Cluster | Operation | Examples | Gloss |
|---------|-----------|----------|-------|
| **st-** | stream() + instantiate() | stop, stand, strict | "flow brought to point" |
| **tr-** | instantiate() + rotate() | tree, true, matrix | "structural rotation" |
| **pl-** | present() + align() | place, plane, apply | "present in alignment" |
| **str-** | stream() + instantiate() + rotate() | string, strong, structure | "flow→pin→stabilize" |
| **spr-** | stream() + present() + rotate() | spring, spread, spray | "flow→emerge→distribute" |


## Falsifiable Predictions

1. **Operator Clustering:** Words with initial sk-/sc- will over-index on "edge/split/scan/classify" semantics vs baseline clusters (p < 0.001)

2. **Vowel Type Priors:** In minimal pairs, vowel substitution will shift meaning predictably:
   - a→i: base→index (*pat→pit*, *man→min*)
   - o→u: container→channel (*for→fur*, *pot→put*)

3. **Geometric Priming:** Exposure to b will prime left-boundary concepts faster than d (right-boundary), controlling for frequency

4. **Metathesis Robustness:** Comprehension of ask/aks, wasp/waps will show identical neural activation patterns in operator-processing regions


## Implementation Notes

```python
# Pseudo-code for operator-payload factorization
def decode_word(surface):
    operators = extract_consonant_clusters(surface)
    payloads = extract_vowel_sequence(surface)
    
    program = []
    for op in operators:
        program.append(OPERATOR_MAP[op])
    
    typed_data = []
    for vowel in payloads:
        typed_data.append(PAYLOAD_MAP[vowel])
    
    return compose(program, typed_data)
```


## Next Steps

- Validate operator mappings against etymological databases
- Test vowel-type priors in sense disambiguation tasks
- Measure geometric priming effects in visual search
- Extend to non-Latin scripts (test universality)


---

*This model treats glyphs as having evolved under selection pressure to efficiently encode meaning through their geometric and articulatory properties. The consistency of these patterns across etymology, dialectal variation, and linguistic families suggests these are not arbitrary but reflect deep structural constraints on how meaning can be efficiently encoded and transmitted.*