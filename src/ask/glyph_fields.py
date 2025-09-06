# /Users/preston/Projects/A-S-K/src/ask/glyphs_fields.py

"""
Field-based glyph operator system with confidence tracking.
Each consonant maps to a field of related operations rather than a single function.
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import json
from pathlib import Path

@dataclass
class OperatorTag:
    """A single operational meaning with confidence"""
    tag: str
    confidence: float  # 0.0 to 1.0
    evidence_count: int = 0
    contexts: List[str] = field(default_factory=list)  # Example words
    
    def update_confidence(self, delta: float, context: str = None):
        """Update confidence based on new evidence"""
        self.evidence_count += 1
        if context and context not in self.contexts[:10]:  # Keep top 10 examples
            self.contexts.append(context)
        # Weighted average: new evidence has less impact as evidence accumulates
        weight = 1.0 / (self.evidence_count + 1)
        self.confidence = (self.confidence * (1 - weight)) + ((self.confidence + delta) * weight)
        self.confidence = max(0.0, min(1.0, self.confidence))  # Clamp to [0,1]

@dataclass 
class OperatorField:
    """A field of related operations for a consonant"""
    glyph: str
    tags: Dict[str, OperatorTag] = field(default_factory=dict)
    position_preferences: Dict[str, Dict[str, float]] = field(default_factory=dict)
    cluster_behaviors: Dict[str, str] = field(default_factory=dict)
    
    def add_tag(self, tag: str, initial_confidence: float = 0.5):
        """Add a new operational tag to this field"""
        if tag not in self.tags:
            self.tags[tag] = OperatorTag(tag, initial_confidence)
    
    def get_best_tag(self, position: str = None, cluster: str = None) -> Tuple[str, float]:
        """Get most likely tag given context"""
        # Check for cluster override
        if cluster and cluster in self.cluster_behaviors:
            cluster_tag = self.cluster_behaviors[cluster]
            if cluster_tag in self.tags:
                return cluster_tag, self.tags[cluster_tag].confidence
        
        # Use position preference if available
        if position and position in self.position_preferences:
            prefs = self.position_preferences[position]
            best_tag = max(prefs.items(), key=lambda x: x[1] * self.tags.get(x[0], OperatorTag('', 0)).confidence)
            if best_tag[0] in self.tags:
                return best_tag[0], self.tags[best_tag[0]].confidence
        
        # Return highest confidence tag
        if self.tags:
            best = max(self.tags.items(), key=lambda x: x[1].confidence)
            return best[0], best[1].confidence
        
        return 'unknown', 0.0

class GlyphFieldSystem:
    """Manages the complete field-based glyph system with confidence tracking"""
    
    # All operator tags in one flat list to avoid bias
    ALL_OPERATOR_TAGS = [
        # Boundary/Container family
        'boundary', 'bulge', 'birth', 'bind', 'base', 'block', 'box',
        
        # Cut/Curve family  
        'curve', 'cut', 'collect', 'cycle', 'call', 'contain', 'carve', 'cleave',
        
        # Define/Direct family
        'define', 'divide', 'direct', 'dense', 'door', 'decide', 'determine',
        
        # Flow/Form family
        'flow', 'fork', 'form', 'force', 'filter', 'flux', 'fashion',
        
        # Gather/Generate family
        'gather', 'generate', 'ground', 'guide', 'gyrate', 'grasp', 'grow',
        
        # Breath/Bridge family
        'breathe', 'bridge', 'height', 'hide', 'hold', 'hover', 'aspirate',
        
        # Junction/Journey family
        'junction', 'journey', 'jut', 'judge', 'jump', 'join', 'jab',
        
        # Cut/Key family (K-specific)
        'key', 'clamp', 'kindle', 'know', 'classify', 'crack',
        
        # Line/Link family
        'line', 'link', 'lift', 'liquid', 'locus', 'extend', 'elevate',
        
        # Matrix/Multiply family
        'matrix', 'multiply', 'mold', 'measure', 'merge', 'memory', 'mother',
        
        # Negate/Navigate family
        'negate', 'navigate', 'new', 'name', 'narrow', 'null', 'next',
        
        # Present/Pulse family
        'present', 'pulse', 'potential', 'point', 'pierce', 'parent', 'push',
        
        # Query/Quest family
        'query', 'quest', 'quantum', 'queue', 'quell', 'quality', 'question',
        
        # Rotate/Resonate family
        'rotate', 'resonate', 'return', 'route', 'rough', 'radiate', 'recursive',
        
        # Stream/Scatter family
        'stream', 'scatter', 'sense', 'separate', 'spiral', 'soft', 'scan',
        
        # Transform/Terminal family
        'transform', 'transcend', 'terminal', 'tool', 'test', 'tree', 'transpose',
        
        # Vector/Valley family
        'vector', 'valley', 'vibrate', 'value', 'view', 'venture', 'void',
        
        # Wave/Web family
        'wave', 'web', 'wander', 'weave', 'wonder', 'witness', 'warp',
        
        # Cross/Exchange family
        'cross', 'exchange', 'execute', 'exact', 'exit', 'examine', 'intersect',
        
        # Yield/Fork family  
        'yield', 'fork', 'why', 'yoke', 'year', 'branch', 'split',
        
        # Zigzag/Zero family
        'zigzag', 'zero', 'zone', 'zenith', 'zephyr', 'zip', 'oscillate'
    ]
    
    def __init__(self, data_path: Optional[Path] = None):
        self.fields: Dict[str, OperatorField] = {}
        self.tag_associations: Dict[str, Dict[str, float]] = defaultdict(dict)  # tag -> {glyph: confidence}
        self.data_path = data_path or Path('/Users/preston/Projects/A-S-K/data/glyph_fields.json')
        self.initialize_fields()
        self.load_confidence_data()
    
    def initialize_fields(self):
        """Initialize operator fields with baseline associations"""
        
        # Define initial field associations with conservative confidence
        initial_associations = {
            'b': {
                'tags': ['boundary', 'bulge', 'birth', 'bind', 'base', 'block'],
                'position_prefs': {
                    'initial': {'birth': 0.7, 'begin': 0.6},
                    'medial': {'bind': 0.7, 'bulge': 0.5},
                    'final': {'boundary': 0.7, 'block': 0.6}
                }
            },
            'c': {
                'tags': ['curve', 'cut', 'collect', 'cycle', 'call', 'contain'],
                'clusters': {'ch': 'channel', 'ck': 'clamp'}
            },
            'd': {
                'tags': ['define', 'divide', 'direct', 'dense', 'door', 'decide'],
                'position_prefs': {
                    'initial': {'define': 0.6, 'direct': 0.6},
                    'final': {'boundary': 0.5, 'end': 0.5}
                }
            },
            'f': {
                'tags': ['flow', 'fork', 'form', 'force', 'filter'],
                'clusters': {'fl': 'flow', 'fr': 'fragment'}
            },
            'g': {
                'tags': ['gather', 'generate', 'ground', 'guide', 'gyrate'],
                'clusters': {'gr': 'ground', 'gh': 'ethereal'}
            },
            'h': {
                'tags': ['breathe', 'bridge', 'height', 'hide', 'hold', 'hover'],
                'modifies': True  # Special marker for modifier
            },
            'j': {
                'tags': ['junction', 'journey', 'jut', 'judge', 'jump', 'join']
            },
            'k': {
                'tags': ['cut', 'key', 'clamp', 'kindle', 'know', 'classify'],
                'clusters': {'sk': 'scan-cut', 'ck': 'terminal-cut'}
            },
            'l': {
                'tags': ['line', 'link', 'lift', 'liquid', 'locus', 'extend']
            },
            'm': {
                'tags': ['matrix', 'multiply', 'mold', 'measure', 'merge', 'memory', 'mother']
            },
            'n': {
                'tags': ['negate', 'navigate', 'new', 'name', 'narrow', 'null']
            },
            'p': {
                'tags': ['present', 'pulse', 'potential', 'point', 'pierce', 'parent'],
                'clusters': {'pr': 'present-recursive', 'pl': 'fold'}
            },
            'q': {
                'tags': ['query', 'quest', 'quantum', 'queue', 'quell', 'quality']
            },
            'r': {
                'tags': ['rotate', 'resonate', 'return', 'route', 'rough', 'radiate', 'recursive']
            },
            's': {
                'tags': ['stream', 'scatter', 'sense', 'separate', 'spiral', 'soft', 'scan'],
                'clusters': {'st': 'establish', 'str': 'structure', 'sh': 'diffuse'}
            },
            't': {
                'tags': ['transform', 'transcend', 'terminal', 'tool', 'test', 'tree'],
                'clusters': {'th': 'ethereal-transform', 'tr': 'transmit'}
            },
            'v': {
                'tags': ['vector', 'valley', 'vibrate', 'value', 'view', 'venture']
            },
            'w': {
                'tags': ['wave', 'web', 'wander', 'weave', 'wonder', 'witness']
            },
            'x': {
                'tags': ['cross', 'exchange', 'execute', 'exact', 'exit', 'examine']
            },
            'y': {
                'tags': ['yield', 'fork', 'why', 'yoke', 'year', 'branch']
            },
            'z': {
                'tags': ['zigzag', 'zero', 'zone', 'zenith', 'zephyr', 'zip']
            }
        }
        
        # Build fields with initial confidence
        for glyph, config in initial_associations.items():
            field_obj = OperatorField(glyph)
            
            # Add tags with baseline confidence
            for tag in config.get('tags', []):
                field_obj.add_tag(tag, initial_confidence=0.5)
                # Track reverse association
                self.tag_associations[tag][glyph] = 0.5
            
            # Add position preferences if specified
            if 'position_prefs' in config:
                field_obj.position_preferences = config['position_prefs']
            
            # Add cluster behaviors if specified  
            if 'clusters' in config:
                field_obj.cluster_behaviors = config['clusters']
            
            self.fields[glyph] = field_obj
    
    def update_tag_confidence(self, glyph: str, tag: str, delta: float, context: str = None):
        """Update confidence for a glyph-tag association"""
        if glyph in self.fields:
            if tag not in self.fields[glyph].tags:
                self.fields[glyph].add_tag(tag, initial_confidence=0.5 + delta)
            else:
                self.fields[glyph].tags[tag].update_confidence(delta, context)
            
            # Update reverse mapping
            self.tag_associations[tag][glyph] = self.fields[glyph].tags[tag].confidence
    
    def get_operator(self, glyph: str, position: str = None, 
                     cluster: str = None, context_word: str = None) -> Tuple[str, float]:
        """Get best operator tag for a glyph in context"""
        if glyph not in self.fields:
            return 'unknown', 0.0
        
        tag, confidence = self.fields[glyph].get_best_tag(position, cluster)
        
        # Optional: track usage for learning
        if context_word:
            self.fields[glyph].tags[tag].contexts.append(context_word)
        
        return tag, confidence
    
    def get_tag_distribution(self, tag: str) -> Dict[str, float]:
        """Get all glyphs associated with a tag and their confidences"""
        return dict(self.tag_associations.get(tag, {}))
    
    def save_confidence_data(self):
        """Persist confidence data to disk"""
        data = {
            'fields': {},
            'tag_associations': dict(self.tag_associations)
        }
        
        for glyph, field_obj in self.fields.items():
            data['fields'][glyph] = {
                'tags': {
                    tag: {
                        'confidence': t.confidence,
                        'evidence_count': t.evidence_count,
                        'contexts': t.contexts[:10]  # Save top 10 examples
                    }
                    for tag, t in field_obj.tags.items()
                },
                'position_preferences': field_obj.position_preferences,
                'cluster_behaviors': field_obj.cluster_behaviors
            }
        
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_confidence_data(self):
        """Load confidence data from disk if it exists"""
        if self.data_path.exists():
            try:
                with open(self.data_path) as f:
                    data = json.load(f)
                
                # Restore fields
                for glyph, field_data in data.get('fields', {}).items():
                    if glyph not in self.fields:
                        self.fields[glyph] = OperatorField(glyph)
                    
                    field_obj = self.fields[glyph]
                    
                    # Restore tags with confidence
                    for tag, tag_data in field_data.get('tags', {}).items():
                        t = OperatorTag(
                            tag=tag,
                            confidence=tag_data['confidence'],
                            evidence_count=tag_data.get('evidence_count', 0),
                            contexts=tag_data.get('contexts', [])
                        )
                        field_obj.tags[tag] = t
                    
                    # Restore preferences
                    field_obj.position_preferences = field_data.get('position_preferences', {})
                    field_obj.cluster_behaviors = field_data.get('cluster_behaviors', {})
                
                # Restore tag associations
                self.tag_associations = defaultdict(dict, data.get('tag_associations', {}))
                
            except Exception as e:
                print(f"Warning: Could not load confidence data: {e}")
    
    def analyze_word(self, word: str) -> List[Tuple[str, str, float]]:
        """Analyze a word and return operator assignments with confidence"""
        results = []
        word_lower = word.lower()
        
        for i, char in enumerate(word_lower):
            if char not in 'aeiou':  # Consonant
                # Determine position
                if i == 0:
                    position = 'initial'
                elif i == len(word_lower) - 1:
                    position = 'final'
                else:
                    position = 'medial'
                
                # Check for clusters
                cluster = None
                if i < len(word_lower) - 1:
                    next_char = word_lower[i + 1]
                    if next_char not in 'aeiou':
                        cluster = char + next_char
                
                tag, confidence = self.get_operator(char, position, cluster, word)
                results.append((char, tag, confidence))
        
        return results
    
    def batch_learn(self, word_analyses: List[Tuple[str, str, str, float]]):
        """
        Learn from batch of analyses.
        Each item is (word, glyph, assigned_tag, confidence_delta)
        """
        for word, glyph, tag, delta in word_analyses:
            self.update_tag_confidence(glyph, tag, delta, word)
        
        self.save_confidence_data()
    
    def report_stats(self) -> Dict:
        """Generate statistics about the current field system"""
        stats = {
            'total_glyphs': len(self.fields),
            'total_unique_tags': len(self.ALL_OPERATOR_TAGS),
            'tags_in_use': len(self.tag_associations),
            'avg_tags_per_glyph': 0,
            'avg_confidence': 0,
            'high_confidence_associations': [],
            'low_confidence_associations': []
        }
        
        total_tags = 0
        total_confidence = 0
        confidence_pairs = []
        
        for glyph, field_obj in self.fields.items():
            total_tags += len(field_obj.tags)
            for tag, tag_obj in field_obj.tags.items():
                total_confidence += tag_obj.confidence
                confidence_pairs.append((glyph, tag, tag_obj.confidence))
        
        if self.fields:
            stats['avg_tags_per_glyph'] = total_tags / len(self.fields)
        
        if confidence_pairs:
            stats['avg_confidence'] = total_confidence / len(confidence_pairs)
            confidence_pairs.sort(key=lambda x: x[2], reverse=True)
            stats['high_confidence_associations'] = confidence_pairs[:10]
            stats['low_confidence_associations'] = confidence_pairs[-10:]
        
        return stats


# Enhanced decoder using field system
class FieldBasedDecoder:
    """Decoder that uses the field-based glyph system"""
    
    def __init__(self, glyph_system: GlyphFieldSystem = None):
        self.glyph_system = glyph_system or GlyphFieldSystem()
    
    def decode_word(self, word: str) -> Dict:
        """Decode a word using field-based operators"""
        word_lower = word.lower()
        operators = []
        payloads = []
        confidences = []
        operator_tags = []
        
        i = 0
        while i < len(word_lower):
            char = word_lower[i]
            
            if char in 'aeiou':
                # Vowel payload
                payloads.append(char)
                i += 1
            else:
                # Consonant operator
                # Determine position
                if i == 0:
                    position = 'initial'
                elif i == len(word_lower) - 1:
                    position = 'final'  
                else:
                    position = 'medial'
                
                # Check for cluster
                cluster = None
                if i < len(word_lower) - 1 and word_lower[i + 1] not in 'aeiou':
                    cluster = char + word_lower[i + 1]
                
                tag, confidence = self.glyph_system.get_operator(char, position, cluster, word)
                
                operators.append(char)
                operator_tags.append(tag)
                confidences.append(confidence)
                
                # Find associated payload
                # Advance by one to allow subsequent consonants to be processed
                i += 1
        
        # Calculate overall confidence
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {    
            'word': word,
            'operators': operators,
            'operator_tags': operator_tags,
            'payloads': payloads,
            'confidences': confidences,
            'overall_confidence': overall_confidence,
            'field_analysis': self.glyph_system.analyze_word(word)
        }
    
    def learn_from_feedback(self, word: str, corrections: List[Tuple[str, str, float]]):
        """
        Learn from user corrections.
        corrections = [(glyph, correct_tag, confidence_boost)]
        """
        analyses = [(word, g, t, c) for g, t, c in corrections]
        self.glyph_system.batch_learn(analyses)
