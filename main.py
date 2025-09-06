from __future__ import annotations

from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator


# -----------------------------
# Enums
# -----------------------------

class LayerARole(str, Enum):
    primitive_operator = "primitive_operator"
    suffix_marker = "suffix_marker"
    channel = "channel"
    none_ = "none"


class DSLCategory(str, Enum):
    nuclear = "nuclear"
    direction_topology = "direction_topology"
    nuclear_proposed = "nuclear_proposed"
    none_ = "none"


class Precedence(str, Enum):
    seed_identity = "seed_identity"
    orthogonality = "orthogonality"
    branching = "branching"
    derivation = "derivation"
    property = "property"
    inflection = "inflection"
    none_ = "none"


# -----------------------------
# Models
# -----------------------------

class DSLProperties(BaseModel):
    model_config = ConfigDict(extra="forbid")
    visual_form: Optional[str] = None
    dimensionality: Optional[int] = None
    orthogonality_required: Optional[bool] = None


class DSLOperatorVariant(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    category: DSLCategory
    precedence: Optional[Precedence] = None
    description: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    operations: Optional[List[str]] = None
    algebraic_laws: Optional[List[str]] = None
    notes: Optional[str] = None


class CompoundParticipation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pattern: str  # e.g., "TH", "TR", "TS", "ST"
    operation: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class VowelChannelFacet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tag: str
    confidence: float = Field(ge=0.0, le=1.0)
    notes: Optional[str] = None


class LayerA(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: LayerARole
    operator_name: Optional[str] = None
    description: Optional[str] = None
    category: DSLCategory = DSLCategory.none_
    precedence: Precedence = Precedence.none_
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    properties: Optional[DSLProperties] = None
    variants: Optional[List[DSLOperatorVariant]] = None
    compounds: Optional[List[CompoundParticipation]] = None
    vowel_channel: Optional[VowelChannelFacet] = None


class PhoneticProperties(BaseModel):
    model_config = ConfigDict(extra="forbid")
    articulation: Optional[str] = None
    breath_requirement: Optional[str] = None
    stop_type: Optional[str] = None


class LayerB(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = None
    semantics: Optional[List[str]] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    evidence: Optional[List[str]] = None
    examples: Optional[List[str]] = None
    phonetic_properties: Optional[PhoneticProperties] = None
    properties: Optional[DSLProperties] = None
    uncertainty_notes: Optional[str] = None


class Letter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: str = Field(pattern=r"^[A-Z]$")
    display_name: Optional[str] = None
    layer_a: Optional[LayerA] = None
    layer_b: Optional[LayerB] = None
    notes: Optional[str] = None

    @field_validator("symbol")
    @classmethod
    def uppercase_letter(cls, v: str) -> str:
        if len(v) != 1 or not v.isalpha() or not v.isupper():
            raise ValueError("symbol must be a single uppercase A–Z letter")
        return v


# -----------------------------
# Instances for all 26 letters
# -----------------------------

LETTERS: Dict[str, Letter] = {
    # I
    "I": Letter(
        symbol="I",
        display_name="I",
        layer_a=LayerA(
            role=LayerARole.primitive_operator,
            operator_name="Seed/Identity/Index",
            description="Seed origin point; identity map; minimal index.",
            category=DSLCategory.nuclear,
            precedence=Precedence.seed_identity,
            properties=DSLProperties(visual_form="line_or_point", dimensionality=0, orthogonality_required=False),
            variants=[
                DSLOperatorVariant(
                    id="i0",
                    name="Seed",
                    category=DSLCategory.nuclear,
                    precedence=Precedence.seed_identity,
                    description="Emit a seed/origin point without allocating axes.",
                    confidence=0.85,
                    operations=["create_origin_point"],
                    algebraic_laws=["Neutral seeding context"]
                ),
                DSLOperatorVariant(
                    id="iId",
                    name="Identity",
                    category=DSLCategory.nuclear,
                    precedence=Precedence.seed_identity,
                    description="Identity map; pass-through.",
                    confidence=0.85,
                    operations=["identity_pass_through"],
                    algebraic_laws=["Left/right identity: iId ∘ f = f ∘ iId = f"]
                ),
                DSLOperatorVariant(
                    id="iIdx",
                    name="Index",
                    category=DSLCategory.nuclear,
                    precedence=Precedence.seed_identity,
                    description="Attach a minimal index/tag.",
                    confidence=0.85,
                    operations=["attach_index"]
                ),
            ],
            vowel_channel=VowelChannelFacet(tag="index", confidence=0.65, notes="Engineered channel tag for T-ops parameterization."),
        ),
        layer_b=LayerB(
            name="Prime Reference",
            semantics=["self_reference", "origin_point", "existence_declaration"],
            confidence=0.95,
            evidence=[
                "Always capitalized in English (unique)",
                "Visual resembles line/point",
                "First-person singular prominence in many languages"
            ],
            examples=["I", "In", "It", "Is", "Idea"],
            phonetic_properties=PhoneticProperties(articulation="minimal", breath_requirement="low", stop_type="none"),
            properties=DSLProperties(visual_form="line_or_point", dimensionality=0, orthogonality_required=False),
        ),
        notes="Layer A = engineered primitives; Layer B = phonosemantic hypothesis.",
    ),

    # T
    "T": Letter(
        symbol="T",
        display_name="T",
        layer_a=LayerA(
            role=LayerARole.primitive_operator,
            operator_name="Orthogonality Constructor",
            description="Allocate an orthogonal axis; support projection, rotation, and sectioning on ⟂.",
            category=DSLCategory.direction_topology,
            precedence=Precedence.orthogonality,
            properties=DSLProperties(visual_form="perpendicular_lines", dimensionality=3, orthogonality_required=True),
            variants=[
                DSLOperatorVariant(
                    id="T",
                    name="Orthogonality Constructor",
                    category=DSLCategory.direction_topology,
                    precedence=Precedence.orthogonality,
                    description="Allocate orthogonal axis relative to current basis.",
                    confidence=0.90,
                    operations=["allocate_axis"]
                ),
                DSLOperatorVariant(
                    id="Th",
                    name="Smoothed Projection",
                    category=DSLCategory.direction_topology,
                    precedence=Precedence.orthogonality,
                    description="Project onto ⟂ with smoothing/attenuation.",
                    confidence=0.75,
                    operations=["project_smooth"]
                ),
                DSLOperatorVariant(
                    id="Tr",
                    name="Orthogonal Rotation",
                    category=DSLCategory.direction_topology,
                    precedence=Precedence.orthogonality,
                    description="Rotate in plane spanned by axis and ⟂.",
                    confidence=0.80,
                    operations=["rotate_plane"]
                ),
                DSLOperatorVariant(
                    id="Ts",
                    name="Orthogonal Section/Snap",
                    category=DSLCategory.direction_topology,
                    precedence=Precedence.orthogonality,
                    description="Slice/quantize along ⟂.",
                    confidence=0.80,
                    operations=["slice_partition", "quantize"]
                ),
                DSLOperatorVariant(
                    id="Tm",
                    name="Reflection (Experimental)",
                    category=DSLCategory.nuclear_proposed,
                    precedence=Precedence.orthogonality,
                    description="Reflect across ⟂.",
                    confidence=0.55,
                    operations=["reflect"],
                    algebraic_laws=["Involution: Tm ∘ Tm = Identity"]
                ),
                DSLOperatorVariant(
                    id="Tl",
                    name="Lift/Embed (Experimental)",
                    category=DSLCategory.nuclear_proposed,
                    precedence=Precedence.orthogonality,
                    description="Embed into higher-dimensional space along ⟂.",
                    confidence=0.50,
                    operations=["embed_lift"]
                ),
                DSLOperatorVariant(
                    id="Tq",
                    name="Orthogonal Query (Experimental)",
                    category=DSLCategory.nuclear_proposed,
                    precedence=Precedence.orthogonality,
                    description="Extract feature along ⟂.",
                    confidence=0.50,
                    operations=["query_feature"]
                ),
            ],
            compounds=[
                CompoundParticipation(pattern="TH", operation="breathe_into_orthogonal_space", confidence=0.85),
                CompoundParticipation(pattern="TR", operation="crystallize_in_perpendicular_dimension", confidence=0.80),
                CompoundParticipation(pattern="TS", operation="stream/snap_through_orthogonal_space", confidence=0.75),
                CompoundParticipation(pattern="ST", operation="stream_into_orthogonality", confidence=0.70),
            ],
        ),
        layer_b=LayerB(
            name="Orthogonality Operator",
            semantics=["create_perpendicular_dimension", "establish_reference_frame", "dimensional_pivot"],
            confidence=0.92,
            evidence=[
                "Visual shape suggests perpendicular lines",
                "Stop articulation blocks flow (alveolar stop)",
            ],
            examples=["Time", "True", "The", "To", "That"],
            phonetic_properties=PhoneticProperties(articulation="stop", breath_requirement="blocked", stop_type="alveolar"),
            properties=DSLProperties(visual_form="perpendicular_lines", dimensionality=3, orthogonality_required=True),
        ),
    ),

    # Y
    "Y": Letter(
        symbol="Y",
        display_name="Y",
        layer_a=LayerA(
            role=LayerARole.primitive_operator,
            operator_name="Fork/Join/Gate",
            description="Branching/selection operators (bifurcation, merge, select).",
            category=DSLCategory.nuclear,
            precedence=Precedence.branching,
            properties=DSLProperties(visual_form="splitting_fork", dimensionality=2, orthogonality_required=False),
            variants=[
                DSLOperatorVariant(
                    id="Yfork",
                    name="Fork (Bifurcation)",
                    category=DSLCategory.nuclear,
                    precedence=Precedence.branching,
                    description="Duplicate and diverge the current object.",
                    confidence=0.80,
                    operations=["fork"]
                ),
                DSLOperatorVariant(
                    id="Yjoin",
                    name="Join (Merge)",
                    category=DSLCategory.nuclear,
                    precedence=Precedence.branching,
                    description="Merge branches using resolver φ.",
                    confidence=0.80,
                    operations=["merge"]
                ),
                DSLOperatorVariant(
                    id="Ygate",
                    name="Gate (Select)",
                    category=DSLCategory.nuclear,
                    precedence=Precedence.branching,
                    description="Select branch by condition.",
                    confidence=0.80,
                    operations=["select"]
                ),
            ],
        ),
        layer_b=LayerB(
            name="Bifurcation Operator",
            semantics=["create_duality", "split_from_unity", "establish_other"],
            confidence=0.88,
            evidence=[
                "Visual shape shows split",
                "Glide articulation mediates transitions"
            ],
            examples=["You", "Yes", "Yang", "Yin", "Why"],
            phonetic_properties=PhoneticProperties(articulation="glide", breath_requirement="medium", stop_type="none"),
            properties=DSLProperties(visual_form="splitting_fork", dimensionality=2, orthogonality_required=False),
        ),
    ),

    # O
    "O": Letter(
        symbol="O",
        display_name="O",
        layer_a=LayerA(
            role=LayerARole.channel,
            vowel_channel=VowelChannelFacet(tag="object", confidence=0.65, notes="Whole/object channel tag for T-ops."),
        ),
        layer_b=LayerB(
            name="Enclosure Operator",
            semantics=["enclose", "complete_cycle", "contain_whole"],
            confidence=0.85,
            evidence=[
                "Circular visual and lip rounding",
                "Zero/Origin/Whole associations"
            ],
            examples=["One", "Whole", "Om", "Zero", "Complete"],
            phonetic_properties=PhoneticProperties(articulation="rounded", breath_requirement="medium", stop_type="none"),
            properties=DSLProperties(visual_form="circle", dimensionality=2, orthogonality_required=False),
        ),
    ),

    # A
    "A": Letter(
        symbol="A",
        display_name="A",
        layer_a=LayerA(
            role=LayerARole.channel,
            vowel_channel=VowelChannelFacet(tag="base", confidence=0.65, notes="Base/origin channel tag for T-ops."),
        ),
        layer_b=LayerB(
            name="Opening/Expansion Operator",
            semantics=["primal_opening", "maximum_aperture", "base_state_establishment"],
            confidence=0.82,
            evidence=[
                "First letter in many alphabets",
                "Ah as primal open vowel"
            ],
            examples=["All", "Any", "And", "Alpha", "Father"],
            phonetic_properties=PhoneticProperties(articulation="open", breath_requirement="maximum", stop_type="none"),
            properties=DSLProperties(visual_form="triangle_peak", dimensionality=1, orthogonality_required=False),
        ),
    ),

    # S
    "S": Letter(
        symbol="S",
        display_name="S",
        layer_a=LayerA(
            role=LayerARole.suffix_marker,
            description="Suffix marker for Ts (section/snap) in DSL composites.",
            compounds=[CompoundParticipation(pattern="TS", operation="slice/quantize along ⟂", confidence=0.80)],
        ),
        layer_b=LayerB(
            name="Stream/Flow Operator",
            semantics=["continuous_flow", "serpentine_movement", "pluralization"],
            confidence=0.78,
            evidence=[
                "Sustained hiss; serpentine curve visually"
            ],
            examples=["Stream", "Swim", "Slide", "Essence", "Serpent"],
            phonetic_properties=PhoneticProperties(articulation="fricative", breath_requirement="continuous", stop_type="none"),
            uncertainty_notes="Some contradictions in usage patterns"
        ),
        notes="DSL: acts as Ts suffix; phonosemantics: flow/stream tendency (defeasible).",
    ),

    # H
    "H": Letter(
        symbol="H",
        display_name="H",
        layer_a=LayerA(
            role=LayerARole.suffix_marker,
            description="Suffix marker for Th (smoothed projection) in DSL composites.",
            compounds=[CompoundParticipation(pattern="TH", operation="breathe_into_orthogonal_space", confidence=0.85)],
        ),
        layer_b=LayerB(
            name="Breath/Animation Operator",
            semantics=["aspirate", "breathe_life", "animate"],
            confidence=0.75,
            evidence=[
                "Pure breath sound; often silent in orthographies"
            ],
            examples=["Holy", "Whole", "Breath", "Heaven", "Heart"],
            phonetic_properties=PhoneticProperties(articulation="aspirate", breath_requirement="pure", stop_type="none"),
            uncertainty_notes="Inconsistent across languages"
        ),
        notes="DSL: suffix-only; phonosemantics: breath/animation tendency.",
    ),

    # R
    "R": Letter(
        symbol="R",
        display_name="R",
        layer_a=LayerA(
            role=LayerARole.suffix_marker,
            description="Suffix marker for Tr (rotation) in DSL composites.",
            compounds=[CompoundParticipation(pattern="TR", operation="rotate/crystallize in ⟂ plane", confidence=0.80)],
        ),
        layer_b=LayerB(
            name="Rotation/Vibration Operator",
            semantics=["rotate", "recurse", "crystallize_through_vibration"],
            confidence=0.73,
            evidence=[
                "Rolled/vibrated tongue gesture"
            ],
            examples=["Rotate", "Return", "Repeat", "Recursive", "Round"],
            phonetic_properties=PhoneticProperties(articulation="liquid_trill", breath_requirement="vibrating", stop_type="none"),
            uncertainty_notes="Many exceptions to pattern"
        ),
        notes="DSL: suffix-only; phonosemantics: rotation/vibration tendency.",
    ),

    # X
    "X": Letter(
        symbol="X",
        display_name="X",
        layer_a=LayerA(
            role=LayerARole.none_,
            description="No primitive role in DSL; can encode 'intersection' as derived (T on multiple channels).",
        ),
        layer_b=LayerB(
            name="Double Orthogonality/Intersection",
            semantics=["double_orthogonality", "mark_intersection", "cancel_through_crossing"],
            confidence=0.68,
            evidence=[
                "Visual: two lines crossing; multiplication mark"
            ],
            examples=["X-ray", "Exit", "Axis", "Matrix"],
            phonetic_properties=PhoneticProperties(articulation="compound_ks", breath_requirement="complex", stop_type="mixed"),
            uncertainty_notes="Limited word samples"
        ),
    ),

    # E
    "E": Letter(
        symbol="E",
        display_name="E",
        layer_a=LayerA(
            role=LayerARole.channel,
            vowel_channel=VowelChannelFacet(tag="relational", confidence=0.65, notes="Edge/relational channel tag for T-ops."),
        ),
        layer_b=LayerB(
            name="Emergence/Narrowing Operator",
            semantics=["directed_emergence", "focused_stream", "narrow_aperture"],
            confidence=0.65,
            evidence=[
                "Mouth narrower than A",
                "Common vowel; hard to isolate"
            ],
            examples=["Emerge", "Energy", "Essence", "Electric", "Element"],
            phonetic_properties=PhoneticProperties(articulation="mid_front", breath_requirement="medium", stop_type="none"),
            uncertainty_notes="Very common; patterns diffuse"
        ),
    ),

    # U
    "U": Letter(
        symbol="U",
        display_name="U",
        layer_a=LayerA(
            role=LayerARole.channel,
            vowel_channel=VowelChannelFacet(tag="capacity", confidence=0.65, notes="Capacity/endurance channel tag for T-ops."),
        ),
        layer_b=LayerB(
            name="Depth/Hidden Operator",
            semantics=["deepen", "hide", "submerge"],
            confidence=0.60,
            evidence=[
                "Back rounded vowel; deep lip posture"
            ],
            examples=["Under", "Unseen", "Underground", "Unconscious"],
            phonetic_properties=PhoneticProperties(articulation="back_rounded", breath_requirement="deep", stop_type="none"),
            uncertainty_notes="Many contradictory uses"
        ),
    ),

    # V
    "V": Letter(
        symbol="V",
        display_name="V",
        layer_a=LayerA(role=LayerARole.none_),
        layer_b=LayerB(
            name="Valley/Convergence Operator",
            semantics=["converge_paths", "create_valley", "funnel_to_point"],
            confidence=0.58,
            evidence=["Visual convergence shape"],
            examples=["Valley", "Converge", "Vector", "Vertex", "Vortex"],
            phonetic_properties=PhoneticProperties(articulation="labiodental_fricative", breath_requirement="directed", stop_type="none"),
            uncertainty_notes="Limited theoretical development"
        ),
    ),

    # L
    "L": Letter(
        symbol="L",
        display_name="L",
        layer_a=LayerA(role=LayerARole.none_),
        layer_b=LayerB(
            name="Flow/Liquid Operator",
            semantics=["directional_flow", "linguistic_liquidity", "lateral_movement"],
            confidence=0.55,
            evidence=["Phonetically 'liquid' class; lateral airflow"],
            examples=["Flow", "Liquid", "Line", "Level", "Lateral"],
            phonetic_properties=PhoneticProperties(articulation="lateral_liquid", breath_requirement="flowing", stop_type="none"),
            uncertainty_notes="Needs more investigation"
        ),
    ),

    # N
    "N": Letter(
        symbol="N",
        display_name="N",
        layer_a=LayerA(role=LayerARole.none_),
        layer_b=LayerB(
            name="Negation/Continuation Operator",
            semantics=["negate", "continue_infinitely", "nasal_resonance"],
            confidence=0.52,
            evidence=["'No/Not' patterns in some families; nasal resonance"],
            examples=["No", "Not", "Never", "And", "On"],
            phonetic_properties=PhoneticProperties(articulation="nasal", breath_requirement="nasal_flow", stop_type="nasal_stop"),
            uncertainty_notes="Dual nature unclear; strong areal/etymological effects"
        ),
    ),

    # M
    "M": Letter(
        symbol="M",
        display_name="M",
        layer_a=LayerA(role=LayerARole.none_),
        layer_b=LayerB(
            name="Material/Mother Operator",
            semantics=["materialize", "manifest", "maternal_creation"],
            confidence=0.50,
            evidence=["Bilabial hum; 'mmm' satisfaction iconicity"],
            examples=["Mother", "Matter", "Make", "Material", "Manifest"],
            phonetic_properties=PhoneticProperties(articulation="bilabial_nasal", breath_requirement="humming", stop_type="bilabial"),
            uncertainty_notes="Broad usage; many exceptions"
        ),
    ),

    # C
    "C": Letter(
        symbol="C",
        display_name="C",
        layer_a=LayerA(role=LayerARole.none_),
        layer_b=LayerB(
            name="Containment/Holding (hypothesis)",
            semantics=["contain", "hold", "capture"],
            confidence=0.55,
            evidence=["Used in 'cat' deconstruction; general phonosemantic claims"],
            examples=["cup", "contain", "capture", "keep (with K)"],
            phonetic_properties=PhoneticProperties(articulation="stop_or_affricate", breath_requirement="blocked_or_partial", stop_type="varies"),
            uncertainty_notes="Untested within the engineered DSL; orthography confounds"
        ),
        notes="From earlier axiom set; not included as a DSL primitive.",
    ),

    # K
    "K": Letter(
        symbol="K",
        display_name="K",
        layer_a=LayerA(role=LayerARole.none_),
        layer_b=LayerB(
            name="Containment/Holding (hypothesis)",
            semantics=["contain", "hold", "capture"],
            confidence=0.55,
            evidence=["Hard boundary; vessel metaphors"],
            examples=["keep", "kernel", "keg", "kit"],
            phonetic_properties=PhoneticProperties(articulation="velar_stop", breath_requirement="blocked", stop_type="velar"),
            uncertainty_notes="Not formalized in DSL; language-specific variation"
        ),
        notes="Paired with C in earlier hypothesis.",
    ),

    # Remaining letters untheorized in this framework: B, D, F, G, J, P, Q, W, Z
    "B": Letter(symbol="B", display_name="B", layer_a=LayerA(role=LayerARole.none_), layer_b=None, notes="Untheorized in current spec."),
    "D": Letter(symbol="D", display_name="D", layer_a=LayerA(role=LayerARole.none_), layer_b=None, notes="Untheorized in current spec."),
    "F": Letter(symbol="F", display_name="F", layer_a=LayerA(role=LayerARole.none_), layer_b=None, notes="Untheorized in current spec."),
    "G": Letter(symbol="G", display_name="G", layer_a=LayerA(role=LayerARole.none_), layer_b=None, notes="Untheorized in current spec."),
    "J": Letter(symbol="J", display_name="J", layer_a=LayerA(role=LayerARole.none_), layer_b=None, notes="Untheorized in current spec."),
    "P": Letter(symbol="P", display_name="P", layer_a=LayerA(role=LayerARole.none_), layer_b=None, notes="Untheorized in current spec."),
    "Q": Letter(symbol="Q", display_name="Q", layer_a=LayerA(role=LayerARole.none_), layer_b=None, notes="Untheorized in current spec."),
    "W": Letter(symbol="W", display_name="W", layer_a=LayerA(role=LayerARole.none_), layer_b=None, notes="Untheorized in current spec."), # manually fixed
    "Z": Letter(symbol="Z", display_name="Z", layer_a=LayerA(role=LayerARole.none_), layer_b=None, notes="Untheorized in current spec.") # manually fixed``
}

# Fix two entries created with wrong type above due to shorthand:

# Fix two entries created with wrong type above due to shorthand:
# LETTERS["W"] = Letter(symbol="W", display_name="W", layer_a=LayerA(role=LayerARole.none_), layer_b=None, notes="Untheorized in current spec.")
# LETTERS["Z"] = Letter(symbol="Z", display_name="Z", layer_a=LayerA(role=LayerARole.none_), layer_b=None, notes="Untheorized in current spec.")



# Optional: quick dump helper
if __name__ == "__main__":
    import json
    print(json.dumps({k: v.model_dump(mode="json") for k, v in LETTERS.items()}, indent=2))
