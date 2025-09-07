"""
CLI for USK syntax with state awareness and multiple output formats
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from pathlib import Path
import json

from ask.state_syntax import USKParser, LatinStateParser, ElementType

console = Console()

@click.group()
def cli():
    """USK Parser with state awareness and syntax generation"""
    pass

@cli.command()
@click.argument('word')
@click.option('--language', '-l', default='english', help='Language: english, latin')
@click.option('--word-type', '-t', default='unknown', help='Word type: noun, verb, adj, etc.')
@click.option('--syntax-only', '-s', is_flag=True, help='Show only USK syntax')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed analysis')
def parse(word, language, word_type, syntax_only, verbose):
    """Parse a word into USK syntax"""
    parser = USKParser()
    result = parser.parse_word(word, language, word_type)
    
    if syntax_only:
        console.print(result.to_usk_syntax())
        return
    
    # Display word header
    console.print(f"\\n[bold cyan]USK Analysis:[/bold cyan] {word}")
    if language != 'english' or word_type != 'unknown':
        console.print(f"[dim]Language: {language}, Type: {word_type}[/dim]")
    
    # Show USK syntax prominently
    syntax_panel = Panel(
        f"[green]{result.to_usk_syntax()}[/green]",
        title="[bold]USK Syntax[/bold]",
        border_style="green"
    )
    console.print(syntax_panel)
    
    if verbose:
        # Detailed element breakdown
        table = Table(title="Element Analysis")
        table.add_column("Surface", style="cyan")
        table.add_column("Type", style="yellow") 
        table.add_column("Semantic", style="green")
        table.add_column("Position", style="blue")
        table.add_column("Confidence", style="magenta")
        table.add_column("State", style="red")
        
        for elem in result.elements:
            state_str = str(elem.state) if elem.state else "—"
            table.add_row(
                elem.surface,
                elem.element_type.value,
                elem.semantic,
                elem.position,
                f"{elem.confidence:.1%}",
                state_str
            )
        
        console.print(table)
        
        # Overall metrics
        console.print(f"\\n[bold]Overall Confidence:[/bold] {result.overall_confidence:.1%}")
        if result.morphology:
            morph_str = ", ".join([f"{k}: {v}" for k, v in result.morphology.items()])
            console.print(f"[bold]Morphology:[/bold] {morph_str}")

@cli.command()
@click.argument('words', nargs=-1)
@click.option('--language', '-l', default='english', help='Language for all words')
@click.option('--format', '-f', type=click.Choice(['syntax', 'table', 'json']), default='syntax')
def batch(words, language, format):
    """Parse multiple words at once"""
    if not words:
        console.print("[red]Please provide at least one word[/red]")
        return
    
    parser = USKParser()
    results = []
    
    for word in words:
        result = parser.parse_word(word, language)
        results.append(result)
    
    if format == 'syntax':
        for word, result in zip(words, results):
            console.print(f"{word} -> {result.to_usk_syntax()}")
    
    elif format == 'table':
        table = Table(title=f"Batch USK Analysis ({language})")
        table.add_column("Word", style="cyan")
        table.add_column("USK Syntax", style="green")
        table.add_column("Confidence", style="magenta")
        table.add_column("Elements", style="yellow")
        
        for word, result in zip(words, results):
            table.add_row(
                word,
                result.to_usk_syntax(),
                f"{result.overall_confidence:.0%}",
                str(len(result.elements))
            )
        
        console.print(table)
    
    elif format == 'json':
        output = []
        for word, result in zip(words, results):
            output.append({
                'word': word,
                'usk_syntax': result.to_usk_syntax(),
                'confidence': result.overall_confidence,
                'elements': [
                    {
                        'surface': e.surface,
                        'type': e.element_type.value,
                        'semantic': e.semantic,
                        'confidence': e.confidence,
                        'state': str(e.state) if e.state else None
                    }
                    for e in result.elements
                ]
            })
        console.print(json.dumps(output, indent=2))

@cli.command()
@click.argument('latin_word')
@click.option('--word-type', '-t', default='noun', help='Word type: noun, verb, adj')
def latin(latin_word, word_type):
    """Parse Latin word with grammatical state analysis"""
    parser = USKParser()
    latin_parser = LatinStateParser()
    
    # Parse the word
    result = parser.parse_word(latin_word, 'latin', word_type)
    
    # Separate state analysis
    state = latin_parser.parse_state(latin_word, word_type)
    
    console.print(f"\\n[bold cyan]Latin Analysis:[/bold cyan] {latin_word}")
    
    # USK Syntax
    syntax_panel = Panel(
        f"[green]{result.to_usk_syntax()}[/green]",
        title="[bold]USK Syntax[/bold]",
        border_style="green"
    )
    console.print(syntax_panel)
    
    # Grammatical State
    state_panel = Panel(
        f"Gender: {state.gender.value}\\n"
        f"Number: {state.number.value}\\n" 
        f"Case: {state.case.value}",
        title="[bold]Grammatical State[/bold]",
        border_style="blue"
    )
    console.print(state_panel)
    
    # Element breakdown
    table = Table(title="Elements with State")
    table.add_column("Surface", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Semantic", style="green")
    table.add_column("State", style="red")
    
    for elem in result.elements:
        state_str = str(elem.state) if elem.state else "—"
        table.add_row(
            elem.surface,
            elem.element_type.value, 
            elem.semantic,
            state_str
        )
    
    console.print(table)

@cli.command()
@click.argument('pattern')
def test_pattern(pattern):
    """Test USK syntax patterns"""
    test_cases = {
        'pronouns': ['I', 'you', 'he', 'she', 'it', 'we', 'they'],
        'modals': ['would', 'could', 'should', 'might', 'will'],
        'questions': ['who', 'what', 'where', 'when', 'why', 'how'],
        'latin_nouns': ['puella', 'dominus', 'templum', 'rex', 'homo'],
        'latin_verbs': ['amat', 'videt', 'audit', 'scribit', 'legit'],
        'structure': ['strict', 'strong', 'string', 'structure', 'construct'],
        'compound': ['understand', 'overcome', 'transform', 'interact']
    }
    
    if pattern not in test_cases:
        console.print(f"[red]Unknown pattern: {pattern}[/red]")
        console.print(f"Available: {', '.join(test_cases.keys())}")
        return
    
    parser = USKParser()
    words = test_cases[pattern]
    language = 'latin' if pattern.startswith('latin') else 'english'
    
    console.print(f"\\n[bold cyan]Testing Pattern:[/bold cyan] {pattern}")
    
    table = Table()
    table.add_column("Word", style="cyan")
    table.add_column("USK Syntax", style="green") 
    table.add_column("Confidence", style="magenta")
    
    for word in words:
        result = parser.parse_word(word, language)
        table.add_row(
            word,
            result.to_usk_syntax(),
            f"{result.overall_confidence:.0%}"
        )
    
    console.print(table)

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file path')
@click.option('--language', '-l', default='english')
@click.option('--syntax-only', '-s', is_flag=True, help='Output only USK syntax')
def file(input_file, output, language, syntax_only):
    """Parse words from a file"""
    parser = USKParser()
    
    # Read input
    words = Path(input_file).read_text().strip().split('\\n')
    words = [w.strip() for w in words if w.strip()]
    
    results = []
    for word in words:
        result = parser.parse_word(word, language)
        if syntax_only:
            results.append(f"{word} -> {result.to_usk_syntax()}")
        else:
            results.append({
                'word': word,
                'usk_syntax': result.to_usk_syntax(),
                'confidence': result.overall_confidence,
                'elements': len(result.elements)
            })
    
    # Output
    if output:
        output_path = Path(output)
        if syntax_only:
            output_path.write_text('\\n'.join(results))
        else:
            output_path.write_text(json.dumps(results, indent=2))
        console.print(f"[green]Results saved to {output}[/green]")
    else:
        if syntax_only:
            for result in results:
                console.print(result)
        else:
            for result in results:
                console.print(f"{result['word']} -> {result['usk_syntax']} [{result['confidence']:.0%}]")

@cli.command()
def demo():
    """Run demonstration of USK syntax features"""
    parser = USKParser()
    
    demos = [
        ("English", "english", [
            ("this", "Demonstrative pronoun"),
            ("ask", "Core kernel operation"), 
            ("manipulation", "Complex derivation"),
            ("understand", "Compound with prefix"),
            ("would", "Modal auxiliary"),
            ("through", "Complex preposition")
        ]),
        ("Latin", "latin", [
            ("puella", "First declension feminine noun"),
            ("dominus", "Second declension masculine noun"),
            ("templum", "Second declension neuter noun"),
            ("amat", "First conjugation verb"),
            ("magna", "Adjective feminine singular")
        ])
    ]
    
    for section_name, lang, examples in demos:
        console.print(f"\\n[bold yellow]--- {section_name} Examples ---[/bold yellow]")
        
        table = Table()
        table.add_column("Word", style="cyan")
        table.add_column("Description", style="dim")
        table.add_column("USK Syntax", style="green")
        
        for word, desc in examples:
            result = parser.parse_word(word, lang)
            table.add_row(word, desc, result.to_usk_syntax())
        
        console.print(table)

if __name__ == '__main__':
    cli()