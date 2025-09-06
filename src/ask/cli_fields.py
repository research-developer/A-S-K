# /Users/preston/Projects/A-S-K/src/ask/cli_fields.py

"""
CLI for field-based glyph system with learning capabilities
"""

import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from pathlib import Path

from ask.glyph_fields import GlyphFieldSystem, FieldBasedDecoder

console = Console()

@click.group()
def cli():
    """Field-based glyph analysis with confidence tracking"""
    pass

@cli.command()
@click.argument('word')
@click.option('--detailed', '-d', is_flag=True, help='Show detailed field analysis')
def decode(word, detailed):
    """Decode a word using field-based operators"""
    decoder = FieldBasedDecoder()
    result = decoder.decode_word(word)
    
    # Display results
    console.print(f"\n[bold cyan]Decoding:[/bold cyan] {word}")
    
    # Create operator table
    table = Table(title="Operator Analysis")
    table.add_column("Position", style="cyan")
    table.add_column("Glyph", style="yellow")
    table.add_column("Operation", style="green")
    table.add_column("Confidence", style="magenta")
    
    for i, (op, tag, conf) in enumerate(zip(
        result['operators'], 
        result['operator_tags'],
        result['confidences']
    )):
        position = 'initial' if i == 0 else 'final' if i == len(result['operators'])-1 else 'medial'
        conf_str = f"{conf:.2%}"
        table.add_row(position, op, tag, conf_str)
    
    console.print(table)
    
    # Show payloads
    console.print(f"\n[bold]Payloads:[/bold] {', '.join(result['payloads'])}")
    console.print(f"[bold]Overall Confidence:[/bold] {result['overall_confidence']:.2%}")
    
    if detailed:
        console.print("\n[bold]Field Analysis:[/bold]")
        for glyph, tag, conf in result['field_analysis']:
            console.print(f"  {glyph} → {tag} ({conf:.2%})")

@cli.command()
@click.argument('glyph')
def field(glyph):
    """Show all operations in a glyph's field"""
    system = GlyphFieldSystem()
    
    if glyph not in system.fields:
        console.print(f"[red]Unknown glyph: {glyph}[/red]")
        return
    
    field_obj = system.fields[glyph]
    
    # Create field display
    table = Table(title=f"Field for '{glyph.upper()}'")
    table.add_column("Operation", style="cyan")
    table.add_column("Confidence", style="green")
    table.add_column("Evidence", style="yellow")
    table.add_column("Example Words", style="dim")
    
    for tag, tag_obj in sorted(field_obj.tags.items(), key=lambda x: x[1].confidence, reverse=True):
        examples = ', '.join(tag_obj.contexts[:3]) if tag_obj.contexts else '-'
        table.add_row(
            tag,
            f"{tag_obj.confidence:.2%}",
            str(tag_obj.evidence_count),
            examples
        )
    
    console.print(table)
    
    # Show position preferences
    if field_obj.position_preferences:
        console.print("\n[bold]Position Preferences:[/bold]")
        for pos, prefs in field_obj.position_preferences.items():
            pref_str = ', '.join([f"{t}({p:.1f})" for t, p in prefs.items()])
            console.print(f"  {pos}: {pref_str}")
    
    # Show clusters
    if field_obj.cluster_behaviors:
        console.print("\n[bold]Cluster Behaviors:[/bold]")
        for cluster, behavior in field_obj.cluster_behaviors.items():
            console.print(f"  {cluster} → {behavior}")

@cli.command()
@click.argument('tag')
def tag_dist(tag):
    """Show which glyphs are associated with a tag"""
    system = GlyphFieldSystem()
    dist = system.get_tag_distribution(tag)
    
    if not dist:
        console.print(f"[red]Unknown tag: {tag}[/red]")
        return
    
    table = Table(title=f"Glyphs associated with '{tag}'")
    table.add_column("Glyph", style="cyan")
    table.add_column("Confidence", style="green")
    
    for glyph, conf in sorted(dist.items(), key=lambda x: x[1], reverse=True):
        table.add_row(glyph.upper(), f"{conf:.2%}")
    
    console.print(table)

@cli.command()
def stats():
    """Show system statistics"""
    system = GlyphFieldSystem()
    stats = system.report_stats()
    
    console.print(Panel.fit(
        f"[bold]Glyph Field System Statistics[/bold]\n\n"
        f"Total Glyphs: {stats['total_glyphs']}\n"
        f"Total Unique Tags: {stats['total_unique_tags']}\n"
        f"Tags in Use: {stats['tags_in_use']}\n"
        f"Avg Tags per Glyph: {stats['avg_tags_per_glyph']:.1f}\n"
        f"Avg Confidence: {stats['avg_confidence']:.2%}"
    ))
    
    # High confidence associations
    if stats['high_confidence_associations']:
        table = Table(title="Highest Confidence Associations")
        table.add_column("Glyph", style="cyan")
        table.add_column("Tag", style="green")
        table.add_column("Confidence", style="magenta")
        
        for g, t, c in stats['high_confidence_associations'][:5]:
            table.add_row(g, t, f"{c:.2%}")
        
        console.print(table)

@cli.command()
@click.argument('word')
@click.argument('glyph')
@click.argument('correct_tag')
@click.option('--confidence', '-c', default=0.1, help='Confidence adjustment')
def learn(word, glyph, correct_tag, confidence):
    """Teach the system a correct association"""
    system = GlyphFieldSystem()
    system.update_tag_confidence(glyph, correct_tag, confidence, word)
    system.save_confidence_data()
    
    console.print(f"[green]✓[/green] Learned: {glyph} → {correct_tag} (from '{word}')")
    
    # Show updated confidence
    if glyph in system.fields and correct_tag in system.fields[glyph].tags:
        new_conf = system.fields[glyph].tags[correct_tag].confidence
        console.print(f"New confidence: {new_conf:.2%}")

@cli.command()
@click.argument('words_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file for results')
def batch_decode(words_file, output):
    """Decode a batch of words from file"""
    decoder = FieldBasedDecoder()
    words = Path(words_file).read_text().strip().split('\n')
    
    results = []
    for word in words:
        if word.strip():
            result = decoder.decode_word(word.strip())
            results.append(result)
    
    if output:
        with open(output, 'w') as f:
            json.dump(results, f, indent=2)
        console.print(f"[green]Results saved to {output}[/green]")
    else:
        for r in results:
            console.print(f"{r['word']}: {', '.join(r['operator_tags'])} [{r['overall_confidence']:.0%}]")

if __name__ == '__main__':
    cli()
