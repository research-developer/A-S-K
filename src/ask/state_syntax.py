"""
State-aware syntax for USK with Latin grammatical features and structured output format.
"""

from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

class LatinGender(Enum):
    MASCULINE = "m"
    FEMININE = "f"  
    NEUTER = "n"
    UNKNOWN = "?"

class LatinNumber(Enum):
    SINGULAR = "sg"
    PLURAL = "pl"
    UNKNOWN = "?"

class LatinCase(Enum):
    NOMINATIVE = "nom"  # subject
    GENITIVE = "gen"    # possessive
    DATIVE = "dat"      # indirect object
    ACCUSATIVE = "acc"  # direct object
    ABLATIVE = "abl"    # instrumental/locative
    VOCATIVE = "voc"    # address
    UNKNOWN = "?"

class ElementType(Enum):
    OPERATOR = "operator"      # consonant operation
    PAYLOAD = "value"         # vowel data
    FUNCTION = "function"     # recognized cluster/compound
    MODIFIER = "modifier"     # aspirated/inflection marker
    STATE = "state"          # grammatical state marker

# Centralized color legend for data types (Rich markup color names)
# These colors are referenced throughout for consistent styling.
TYPE_COLORS: Dict[str, str] = {
    "op": "blue",
    "func": "green",
    "val": "yellow",
    "struct": "orange1",
    # Optional extras
    "mod": "magenta",
    "state": "cyan",
}

@dataclass
class LatinState:
    """Grammatical state information for Latin words"""
    gender: LatinGender = LatinGender.UNKNOWN
    number: LatinNumber = LatinNumber.UNKNOWN 
    case: LatinCase = LatinCase.UNKNOWN
    
    def __str__(self) -> str:
        parts = []
        if self.gender != LatinGender.UNKNOWN:
            parts.append(self.gender.value)
        if self.number != LatinNumber.UNKNOWN:
            parts.append(self.number.value)
        if self.case != LatinCase.UNKNOWN:
            parts.append(self.case.value)
        return ".".join(parts) if parts else "?"

@dataclass
class USKElement:
    """A single element in the USK syntax tree"""
    surface: str           # original text
    element_type: ElementType
    semantic: str          # semantic interpretation
    confidence: float = 0.5
    state: Optional[LatinState] = None
    position: str = "medial"  # initial/medial/final
    
    def to_usk_syntax(self) -> str:
        """Convert to USK bracket notation
        New format: {semantic:short_type}[state]
        - short_type: op, func, val; for composite payloads use 'struct'
        - state remains as a suffix in brackets if present
        """
        # Determine short type label
        type_map = {
            ElementType.OPERATOR: "op",
            ElementType.FUNCTION: "func",
            ElementType.PAYLOAD: "val",
            ElementType.MODIFIER: "mod",
            ElementType.STATE: "state",
        }
        short_type = type_map.get(self.element_type, "?")
        semantic = self.semantic or self.surface
        # For composite payloads, display type key as 'struct' for color selection
        if self.element_type == ElementType.PAYLOAD and isinstance(semantic, str) and ('+' in semantic or ',' in semantic):
            short_type = "struct"

        # Base token is semantic only; type is conveyed by color
        token_inner = f"{semantic}"
        # Apply centralized color based on type
        color = TYPE_COLORS.get(short_type, None)
        if short_type == "struct" and color:
            # Color only the braces, not the semantic; avoid f-strings with literal braces
            open_b = "[" + color + "]" + "{" + "[/" + color + "]"
            close_b = "[" + color + "]" + "}" + "[/" + color + "]"
            wrapped = open_b + token_inner + close_b
        else:
            # Color the semantic itself
            colored_inner = f"[{color}]{token_inner}[/{color}]" if color else token_inner
            wrapped = f"{{{colored_inner}}}"

        if self.state and str(self.state) != "?":
            wrapped += f"[{self.state}]"

        return wrapped

@dataclass 
class USKSequence:
    """A sequence of USK elements representing a word or phrase"""
    elements: List[USKElement]
    overall_confidence: float = 0.5
    morphology: Optional[Dict[str, str]] = None
    
    def to_usk_syntax(self) -> str:
        """Convert to USK syntax in strictly linear scan order with no grouping.
        Example: [{elem1}-{elem2}-{elem3}-...]
        """
        if not self.elements:
            return "[]"
        parts = [e.to_usk_syntax() for e in self.elements]
        return f"[{ '-'.join(parts) }]"
    
    def _format_group(self, group: List[USKElement]) -> str:
        """Format a group of related elements"""
        if len(group) <= 1:
            return group[0].to_usk_syntax() if group else ""
        
        # Separate operators and payloads
        operators = [e for e in group if e.element_type == ElementType.OPERATOR]
        payloads = [e for e in group if e.element_type == ElementType.PAYLOAD]
        others = [e for e in group if e.element_type not in [ElementType.OPERATOR, ElementType.PAYLOAD]]
        
        parts = []
        
        # Format operators
        if len(operators) > 1:
            op_strs = [op.to_usk_syntax() for op in operators]
            parts.append("|".join(op_strs))
        elif operators:
            parts.append(operators[0].to_usk_syntax())
        
        # Format payloads in parentheses if they exist
        if payloads:
            payload_strs = [p.to_usk_syntax() for p in payloads]
            parts.append(f"({','.join(payload_strs)})")
        
        # Add other elements
        for other in others:
            parts.append(other.to_usk_syntax())
        
        return "".join(parts)

class LatinStateParser:
    """Parses Latin endings to extract grammatical state"""
    
    # Common Latin ending patterns with their grammatical information
    ENDING_PATTERNS = {
        # First declension (mostly feminine)
        'a': LatinState(LatinGender.FEMININE, LatinNumber.SINGULAR, LatinCase.NOMINATIVE),
        'ae': LatinState(LatinGender.FEMININE, LatinNumber.SINGULAR, LatinCase.GENITIVE),
        'am': LatinState(LatinGender.FEMININE, LatinNumber.SINGULAR, LatinCase.ACCUSATIVE),
        'as': LatinState(LatinGender.FEMININE, LatinNumber.PLURAL, LatinCase.ACCUSATIVE),
        
        # Second declension masculine
        'us': LatinState(LatinGender.MASCULINE, LatinNumber.SINGULAR, LatinCase.NOMINATIVE),
        'i': LatinState(LatinGender.MASCULINE, LatinNumber.SINGULAR, LatinCase.GENITIVE),
        'um': LatinState(LatinGender.MASCULINE, LatinNumber.SINGULAR, LatinCase.ACCUSATIVE),
        'os': LatinState(LatinGender.MASCULINE, LatinNumber.PLURAL, LatinCase.ACCUSATIVE),
        
        # Second declension neuter
        'um': LatinState(LatinGender.NEUTER, LatinNumber.SINGULAR, LatinCase.NOMINATIVE),
        'a': LatinState(LatinGender.NEUTER, LatinNumber.PLURAL, LatinCase.NOMINATIVE),
        
        # Third declension patterns (complex)
        'is': LatinState(LatinGender.UNKNOWN, LatinNumber.SINGULAR, LatinCase.GENITIVE),
        'em': LatinState(LatinGender.UNKNOWN, LatinNumber.SINGULAR, LatinCase.ACCUSATIVE),
        'es': LatinState(LatinGender.UNKNOWN, LatinNumber.PLURAL, LatinCase.NOMINATIVE),
        
        # Common verb endings
        't': LatinState(LatinGender.UNKNOWN, LatinNumber.SINGULAR, LatinCase.UNKNOWN), # 3rd person sg
        'nt': LatinState(LatinGender.UNKNOWN, LatinNumber.PLURAL, LatinCase.UNKNOWN),  # 3rd person pl
    }
    
    def parse_state(self, word: str, word_type: str = "noun") -> LatinState:
        """Extract grammatical state from a Latin word"""
        word_lower = word.lower().strip()
        
        # Try endings from longest to shortest
        endings = sorted(self.ENDING_PATTERNS.keys(), key=len, reverse=True)
        
        for ending in endings:
            if word_lower.endswith(ending) and len(word_lower) > len(ending):
                state = self.ENDING_PATTERNS[ending]
                # TODO: Add logic to disambiguate overlapping endings
                return state
        
        return LatinState()  # Default unknown state

class USKParser:
    """Parses words into USK syntax with state awareness"""
    
    def __init__(self, glyph_system=None):
        from ask.glyph_fields import GlyphFieldSystem
        self.glyph_system = glyph_system or GlyphFieldSystem()
        self.latin_parser = LatinStateParser()
        
        # Common Latin/English function clusters
        self.function_clusters = {
            'th': 'abstract_reference',  # the, that, this
            'wh': 'interrogative',       # who, what, where
            'sh': 'smooth_modifier',     # shall, should
            'ch': 'choice_check',        # check, choose
            'str': 'structure',          # strict, strong, string
            'spr': 'disperse',           # spring, spray, spread
            'qu': 'query',               # question, quiet, quick
        }
    
    def parse_word(self, word: str, language: str = "english", 
                   word_type: str = "unknown") -> USKSequence:
        """Parse a word into USK elements"""
        word_lower = word.lower()
        elements = []
        i = 0
        
        # Parse Latin state if applicable
        latin_state = None
        if language.lower() == "latin":
            latin_state = self.latin_parser.parse_state(word, word_type)
        
        while i < len(word_lower):
            char = word_lower[i]
            
            # Check for function clusters first
            cluster_found = False
            for cluster, function in self.function_clusters.items():
                if word_lower.startswith(cluster, i):
                    # Create function element
                    elem = USKElement(
                        surface=cluster,
                        element_type=ElementType.FUNCTION,
                        semantic=function,
                        confidence=0.8,
                        position="initial" if i == 0 else "final" if i + len(cluster) >= len(word_lower) else "medial"
                    )
                    elements.append(elem)
                    i += len(cluster)
                    cluster_found = True
                    break
            
            if cluster_found:
                continue
            
            if char in 'aeiou':
                # Vowel payload
                # Collect consecutive vowels as one payload
                vowel_run = ""
                j = i
                while j < len(word_lower) and word_lower[j] in 'aeiou':
                    vowel_run += word_lower[j]
                    j += 1
                
                elem = USKElement(
                    surface=vowel_run,
                    element_type=ElementType.PAYLOAD,
                    semantic=self._get_payload_semantic(vowel_run),
                    confidence=0.7,
                    state=latin_state if language.lower() == "latin" else None
                )
                elements.append(elem)
                i = j
            
            elif char.isalpha():
                # Consonant operator
                position = "initial" if i == 0 else "final" if i == len(word_lower) - 1 else "medial"
                
                # Get semantic from glyph system
                tag, confidence = self.glyph_system.get_operator(char, position)
                
                # Check if this is an aspirated consonant (h modifier)
                is_aspirated = (i + 1 < len(word_lower) and 
                              word_lower[i + 1] == 'h' and 
                              char != 'h')
                
                elem_type = ElementType.MODIFIER if char == 'h' else ElementType.OPERATOR
                
                elem = USKElement(
                    surface=char,
                    element_type=elem_type,
                    semantic=tag,
                    confidence=confidence,
                    position=position,
                    state=latin_state if language.lower() == "latin" and i >= len(word_lower) - 3 else None
                )
                elements.append(elem)
                i += 1
            
            else:
                # Skip non-alphabetic characters
                i += 1
        
        # Calculate overall confidence
        confidences = [e.confidence for e in elements if e.confidence > 0]
        overall_conf = sum(confidences) / len(confidences) if confidences else 0.5
        
        return USKSequence(
            elements=elements,
            overall_confidence=overall_conf,
            morphology={"word": word, "language": language, "type": word_type}
        )
    
    def _get_payload_semantic(self, vowel_run: str) -> str:
        """Get semantic interpretation of vowel payload"""
        if len(vowel_run) == 1:
            payload_map = {
                'a': 'a',
                'e': 'relation/edge', 
                'i': 'identify',
                'o': 'container/whole',
                'u': 'channel/depth',
                'y': 'branch/choice'
            }
            return payload_map.get(vowel_run, 'unknown')
        else:
            # Composite payload -> flatten without type label
            parts = [self._get_payload_semantic(v) for v in vowel_run]
            return "+".join(parts)

# Example usage and test functions
def test_usk_syntax():
    """Test the USK syntax generation"""
    parser = USKParser()
    
    # Test "this"
    result = parser.parse_word("this")
    print(f"'this' -> {result.to_usk_syntax()}")
    
    # Test "transformation"
    result = parser.parse_word("transformation")
    print(f"'transformation' -> {result.to_usk_syntax()}")
    
    # Test Latin word
    result = parser.parse_word("puella", language="latin", word_type="noun")
    print(f"'puella' (Latin) -> {result.to_usk_syntax()}")
    
    # Test "manipulation"
    result = parser.parse_word("manipulation")
    print(f"'manipulation' -> {result.to_usk_syntax()}")

def demo_latin_state():
    """Demonstrate Latin grammatical state parsing"""
    latin_parser = LatinStateParser()
    
    test_words = [
        "puella",    # girl (nom sg f)
        "puellae",   # of girl/girls (gen sg f / nom pl f)  
        "puellam",   # girl (acc sg f)
        "dominus",   # lord (nom sg m)
        "domini",    # of lord (gen sg m)
        "dominum",   # lord (acc sg m)
        "templum",   # temple (nom sg n)
        "templa"     # temples (nom pl n)
    ]
    
    for word in test_words:
        state = latin_parser.parse_state(word)
        print(f"{word} -> {state}")

if __name__ == "__main__":
    print("=== USK Syntax Tests ===")
    test_usk_syntax()
    
    print("\n=== Latin State Demo ===")
    demo_latin_state()