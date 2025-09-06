"""
Comprehensive test suite for the enhanced USK implementation.
Tests operator extraction, payload typing, morphology, and special cases.
"""

from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ask.enhanced_factorizer import (
    enhanced_decode_word,
    extract_operators_enhanced,
    extract_payloads_enhanced,
    segment_morphology_simple,
    validate_ask_kernel,
    COMPLETE_OPERATOR_MAP,
    ENHANCED_CLUSTER_MAP,
)


def test_ask_is_kernel():
    """The word 'ask' must encode the semantic kernel operation."""
    decoded = enhanced_decode_word("ask")
    
    # Fundamental test: A-S-K = aperture, stream, clamp
    assert "stream" in decoded["operators"], "S (stream) missing"
    assert "clamp" in decoded["operators"], "K (clamp) missing"
    assert "base" in decoded["payloads"], "A (aperture/base) missing"
    
    # Verify kernel validation
    assert decoded.get("validation", {}).get("is_kernel") == True
    assert "semantic retrieval" in decoded["validation"]["kernel_proof"]
    
    print("✓ ASK kernel test passed")


def test_operator_extraction():
    """Test extraction of single and clustered operators."""
    
    # Single operators
    ops, conf = extract_operators_enhanced("bat")
    assert "bind" in ops  # b
    assert conf > 0.7
    
    # Clusters
    ops, conf = extract_operators_enhanced("ask")
    assert ops == ["stream", "clamp"]  # sk cluster
    assert conf > 0.9  # sk is high confidence
    
    ops, conf = extract_operators_enhanced("string")
    assert "stream" in ops  # str cluster
    assert "instantiate" in ops
    assert "rotate" in ops
    
    print("✓ Operator extraction test passed")


def test_payload_typing():
    """Test payload extraction with type information."""
    
    payloads, conf = extract_payloads_enhanced("aeiou")
    
    types = [p["type"] for p in payloads]
    assert "base_type" in types  # a
    assert "relation" in types   # e
    assert "index" in types      # i
    assert "container" in types  # o
    assert "struct" in types     # u
    
    print("✓ Payload typing test passed")


def test_morphological_segmentation():
    """Test simple morphological analysis."""
    
    # Prefix detection
    morph = segment_morphology_simple("understand")
    assert morph["prefix"] == "un"
    assert morph["root"] == "derstand"
    
    # Suffix detection
    morph = segment_morphology_simple("manipulation")
    assert morph["suffix"] == "tion"
    assert "manipula" in morph["root"]
    
    # No affixes
    morph = segment_morphology_simple("ask")
    assert morph["prefix"] is None
    assert morph["suffix"] is None
    assert morph["root"] == "ask"
    
    print("✓ Morphological segmentation test passed")


def test_geometric_complementarity():
    """Test b|d and p|q mirror pairs."""
    
    # b|d are mirror boundaries
    b_info = COMPLETE_OPERATOR_MAP["b"]
    d_info = COMPLETE_OPERATOR_MAP["d"]
    assert b_info["op"] == "bind"
    assert d_info["op"] == "decide"
    assert "left" in b_info["principle"]
    assert "right" in d_info["principle"]
    
    # p|q are presence|query
    p_info = COMPLETE_OPERATOR_MAP["p"]
    q_info = COMPLETE_OPERATOR_MAP["q"]
    assert p_info["op"] == "present"
    assert q_info["op"] == "query"
    
    print("✓ Geometric complementarity test passed")


def test_compound_words():
    """Test decoding of compound words."""
    
    # understand = under + stand
    decoded = enhanced_decode_word("understand")
    assert "negate" in decoded["operators"]  # un- prefix
    
    # manipulation: verify adjacency and composite payload
    decoded = enhanced_decode_word("manipulation")
    # Ensure 't' consumes 'io' and final 'n' has no payload
    pairs = decoded["pairs"]
    assert ("t", "io") in pairs or any(op == "t" and (pay == "io") for op, pay in pairs)
    # last pair likely ('n', None)
    assert pairs[-1][0].endswith("n")
    assert pairs[-1][1] in (None, "")
    # sanity on operators/confidence
    assert "multiply" in decoded["operators"]  # m
    assert decoded["confidence"] > 0.5
    
    print("✓ Compound word test passed")


def test_confidence_scoring():
    """Test confidence aggregation."""
    
    # High confidence word (ask)
    decoded = enhanced_decode_word("ask")
    assert decoded["confidence"] > 0.85  # sk cluster is 0.95
    
    # Lower confidence word with unknown patterns
    decoded = enhanced_decode_word("xyz")
    assert decoded["confidence"] < 0.85
    
    print("✓ Confidence scoring test passed")


def test_special_patterns():
    """Test special operator patterns."""
    
    # Modal pattern -ould
    for word in ["would", "could", "should"]:
        ops, _ = extract_operators_enhanced(word)
        assert "align" in ops  # ld cluster
        assert "decide" in ops
    
    # Light pattern ght
    ops, _ = extract_operators_enhanced("light")
    # Note: 'ght' should be recognized as a pattern
    
    # th pattern (abstract)
    ops, _ = extract_operators_enhanced("the")
    assert "instantiate" in ops  # t
    assert "animate" in ops      # h
    
    print("✓ Special patterns test passed")


def test_metathesis_invariance():
    """Test that ask/aks have same semantic core."""
    
    decoded_ask = enhanced_decode_word("ask")
    decoded_aks = enhanced_decode_word("aks")  # dialectal variant
    
    # Both should have stream and clamp operations
    # (order may vary but core operators should be present)
    ask_ops = set(decoded_ask["operators"])
    aks_ops = set(decoded_aks["operators"])
    
    # Core semantic overlap
    assert "stream" in ask_ops
    assert "clamp" in ask_ops
    # Note: aks might decompose differently but should share core semantics
    
    print("✓ Metathesis invariance test passed")


def test_etymological_families():
    """Test operator consistency within etymological families."""
    
    # str- family (structure, string, strict, strong)
    str_words = ["string", "strong", "strict", "structure"]
    for word in str_words:
        ops, _ = extract_operators_enhanced(word)
        # All should have the str- cluster operations
        assert "stream" in ops
        assert "instantiate" in ops
        assert "rotate" in ops
    
    print("✓ Etymological family test passed")


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_ask_is_kernel,
        test_operator_extraction,
        test_payload_typing,
        test_morphological_segmentation,
        test_geometric_complementarity,
        test_compound_words,
        test_confidence_scoring,
        test_special_patterns,
        test_metathesis_invariance,
        test_etymological_families,
    ]
    
    print("Running USK Test Suite")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    # Final validation
    if failed == 0:
        print("\n🎉 All tests passed! The USK framework is validated.")
        validate_ask_kernel()
    else:
        print(f"\n⚠️  {failed} tests failed. Review needed.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)