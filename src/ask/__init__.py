"""A-S-K core package.

Provides glyph maps, a simple factorizer that splits operators (consonants) and
payloads (vowels), and composition helpers to build a minimal typed AST.

CLI available at ask.cli
"""

from .glyphs import OPERATOR_MAP, PAYLOAD_MAP, CLUSTER_MAP
from .factorizer import decode_word, extract_consonant_clusters, extract_vowel_sequence
from .compose import compose_token

# Enhanced imports
try:
    from .glyphs_fields import GlyphFieldSystem, FieldBasedDecoder
    from .enhanced_factorizer import enhanced_decode_word
    from .state_syntax import USKParser, LatinStateParser
except ImportError:
    pass  # Optional enhanced features
