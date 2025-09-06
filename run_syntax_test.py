#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ask.state_syntax import USKParser, demo_latin_state

def main():
    print("=== USK Syntax Demo ===\n")
    
    parser = USKParser()
    
    # Test cases with expected outputs
    test_cases = [
        ("this", "english"),
        ("ask", "english"), 
        ("manipulation", "english"),
        ("would", "english"),
        ("through", "english"),
        ("understand", "english"),
        ("puella", "latin"),  # Latin: girl (nom sg f)
        ("dominum", "latin"), # Latin: lord (acc sg m)
    ]
    
    print("WORD -> USK SYNTAX")
    print("-" * 50)
    
    for word, language in test_cases:
        try:
            result = parser.parse_word(word, language)
            syntax = result.to_usk_syntax()
            print(f"{word:12} -> {syntax}")
            
            # Show detailed breakdown for a few examples
            if word in ["this", "ask", "manipulation"]:
                print(f"{'':14}   Elements:")
                for elem in result.elements:
                    state_info = f" [{elem.state}]" if elem.state and str(elem.state) != "?" else ""
                    print(f"{'':14}     {elem.surface} ({elem.element_type.value}: {elem.semantic}){state_info}")
                print()
        except Exception as e:
            print(f"{word:12} -> ERROR: {e}")
    
    print("\n=== Latin State Examples ===")
    try:
        demo_latin_state()
    except Exception as e:
        print(f"Error in Latin demo: {e}")

if __name__ == "__main__":
    main()