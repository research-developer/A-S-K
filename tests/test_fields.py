# /Users/preston/Projects/A-S-K/tests/test_fields.py

"""
Tests for field-based glyph system
"""

import pytest
from pathlib import Path
import tempfile
import json

from ask.glyphs_fields import (
    OperatorTag, OperatorField, GlyphFieldSystem, FieldBasedDecoder
)

def test_operator_tag_confidence_update():
    """Test confidence updating mechanism"""
    tag = OperatorTag('test', 0.5)
    
    # Positive evidence
    tag.update_confidence(0.2, 'example1')
    assert 0.5 < tag.confidence < 0.8
    assert tag.evidence_count == 1
    assert 'example1' in tag.contexts
    
    # More evidence
    tag.update_confidence(0.1, 'example2')
    assert tag.evidence_count == 2
    
    # Negative evidence
    tag.update_confidence(-0.3, 'counter')
    assert tag.confidence < 0.7

def test_operator_field_best_tag():
    """Test tag selection based on context"""
    field = OperatorField('t')
    field.add_tag('transform', 0.7)
    field.add_tag('terminal', 0.5)
    field.add_tag('tool', 0.3)
    
    # Without context
    tag, conf = field.get_best_tag()
    assert tag == 'transform'
    assert conf == 0.7
    
    # With position preference
    field.position_preferences = {
        'final': {'terminal': 0.9}
    }
    tag, conf = field.get_best_tag(position='final')
    assert tag == 'terminal'
    
    # With cluster override
    field.cluster_behaviors = {'th': 'ethereal'}
    field.add_tag('ethereal', 0.4)
    tag, conf = field.get_best_tag(cluster='th')
    assert tag == 'ethereal'

def test_glyph_system_initialization():
    """Test system initializes with baseline fields"""
    system = GlyphFieldSystem()
    
    # Check some expected fields exist
    assert 'b' in system.fields
    assert 'boundary' in system.fields['b'].tags
    assert 't' in system.fields
    assert 'transform' in system.fields['t'].tags
    
    # Check tag associations
    assert 'boundary' in system.tag_associations
    assert 'b' in system.tag_associations['boundary']

def test_confidence_persistence():
    """Test saving and loading confidence data"""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Create system with custom path
        system1 = GlyphFieldSystem(data_path=temp_path)
        
        # Update some confidences
        system1.update_tag_confidence('b', 'boundary', 0.3, 'border')
        system1.update_tag_confidence('t', 'transform', 0.2, 'transmute')
        system1.save_confidence_data()
        
        # Load in new system
        system2 = GlyphFieldSystem(data_path=temp_path)
        
        # Check persistence
        assert 'boundary' in system2.fields['b'].tags
        b_boundary = system2.fields['b'].tags['boundary']
        assert b_boundary.confidence > 0.5
        assert 'border' in b_boundary.contexts
        
    finally:
        temp_path.unlink(missing_ok=True)

def test_field_decoder():
    """Test field-based word decoding"""
    decoder = FieldBasedDecoder()
    
    # Test "ask"
    result = decoder.decode_word('ask')
    assert 's' in result['operators']
    assert 'k' in result['operators']
    assert 'a' in result['payloads']
    assert result['overall_confidence'] > 0
    
    # Test with learning
    decoder.learn_from_feedback('ask', [
        ('s', 'stream', 0.2),
        ('k', 'clamp', 0.2)
    ])
    
    # Decode again - should have higher confidence
    result2 = decoder.decode_word('ask')
    assert result2['overall_confidence'] >= result['overall_confidence']

def test_word_analysis():
    """Test analyzing words for operator positions"""
    system = GlyphFieldSystem()
    
    # Analyze "transform"
    analysis = system.analyze_word('transform')
    
    # Should identify t, r, n, s, f, r, m as operators
    operators = [a[0] for a in analysis]
    assert 't' in operators
    assert 'r' in operators
    assert 'm' in operators
    
    # Check position effects
    # First 't' should be initial position
    t_analyses = [a for a in analysis if a[0] == 't']
    assert len(t_analyses) > 0

def test_batch_learning():
    """Test batch learning from multiple examples"""
    system = GlyphFieldSystem()
    
    # Initial confidence
    initial_conf = system.fields['s'].tags.get('stream', OperatorTag('stream', 0.5)).confidence
    
    # Batch learn
    system.batch_learn([
        ('stream', 's', 'stream', 0.3),
        ('strike', 's', 'stream', 0.2),
        ('slow', 's', 'stream', 0.1),
    ])
    
    # Check confidence increased
    new_conf = system.fields['s'].tags['stream'].confidence
    assert new_conf > initial_conf
    
    # Check contexts recorded
    contexts = system.fields['s'].tags['stream'].contexts
    assert 'stream' in contexts or 'strike' in contexts

def test_tag_distribution():
    """Test getting all glyphs for a tag"""
    system = GlyphFieldSystem()
    
    # Get distribution for 'boundary'
    dist = system.get_tag_distribution('boundary')
    
    # Should have b and potentially d
    assert 'b' in dist
    assert dist['b'] > 0
    
    # Non-existent tag
    dist2 = system.get_tag_distribution('nonexistent')
    assert len(dist2) == 0

def test_stats_reporting():
    """Test statistics generation"""
    system = GlyphFieldSystem()
    stats = system.report_stats()
    
    assert stats['total_glyphs'] > 20  # Should have most letters
    assert stats['total_unique_tags'] == len(system.ALL_OPERATOR_TAGS)
    assert stats['avg_confidence'] > 0
    assert len(stats['high_confidence_associations']) > 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
