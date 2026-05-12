#!/usr/bin/env python3
"""
Fix dotted circle anchors for combining marks in a Glyphs font.
This ensures combining marks can attach to the dotted circle (U+25CC).
"""

import sys
import glyphsLib
import glyphsLib.writer
from glyphsLib.classes import GSAnchor, GSGlyph, GSLayer, GSPath, GSNode


def create_dotted_circle_glyph():
    """Create a dotted circle glyph (U+25CC) with proper shape."""
    
    glyph = GSGlyph()
    glyph.name = 'uni25CC'
    glyph.unicode = '25CC'
    
    # Create a layer with the dotted circle path
    layer = GSLayer()
    layer.associatedMasterId = font.masters[0].id
    
    # Dotted circle: circle with small circles inside
    # Main circle outline
    path = GSPath()
    path.nodes = [
        GSNode((500, 0), 'line'),      # Bottom
        GSNode((1000, 500), 'line'),   # Right
        GSNode((500, 1000), 'line'),   # Top
        GSNode((0, 500), 'line'),      # Left
    ]
    path.closed = True
    
    # Add inner circle (counter-clockwise for hole)
    inner_path = GSPath()
    inner_path.nodes = [
        GSNode((500, 200), 'line'),
        GSNode((800, 500), 'line'),
        GSNode((500, 800), 'line'),
        GSNode((200, 500), 'line'),
    ]
    inner_path.closed = True
    
    layer.paths = [path, inner_path]
    glyph.layers = [layer]
    
    return glyph


def fix_dotted_circle_anchors(glyphs_path, output_path=None):
    """
    Add anchors to dotted circle and combining marks for proper attachment.
    """
    
    global font
    font = glyphsLib.load(glyphs_path)
    
    # Combining marks that need anchors to attach to dotted circle
    combining_marks = [
        'uni031B',  # combining horn
        'uni0328',  # combining ogonek
        'uni0335',  # combining long solidus overlay
        'uni0336',  # combining long strikeout overlay
        'uni0337',  # combining short solidus overlay
        'uni0338',  # combining long slash overlay
    ]
    
    # Check if dotted circle exists
    dotted_circle = None
    for g in font.glyphs:
        if g.name == 'uni25CC':
            dotted_circle = g
            break
    
    if not dotted_circle:
        print("uni25CC (dotted circle) not found - creating it...")
        dotted_circle = create_dotted_circle_glyph()
        font.glyphs.append(dotted_circle)
    
    # Get the bounding box to determine anchor positions
    layer = dotted_circle.layers[0]
    bounds = layer.bounds
    if bounds:
        center_x = bounds.origin.x + bounds.size.width / 2
    else:
        center_x = 500  # Default center for 1000-unit em
    
    # Remove existing anchors
    dotted_circle.anchors = []
    
    # Add anchors to dotted circle
    top_anchor = GSAnchor()
    top_anchor.name = '_top'
    top_anchor.position = (center_x, 700)
    dotted_circle.anchors.append(top_anchor)
    
    bottom_anchor = GSAnchor()
    bottom_anchor.name = '_bottom'
    bottom_anchor.position = (center_x, 0)
    dotted_circle.anchors.append(bottom_anchor)
    
    print(f"Added anchors to uni25CC (dotted circle):")
    print(f"  _top at x={center_x}, y=700")
    print(f"  _bottom at x={center_x}, y=0")
    
    # Add matching anchors to combining marks
    marks_fixed = 0
    for mark_name in combining_marks:
        for g in font.glyphs:
            if g.name == mark_name:
                # Remove existing anchors
                g.anchors = []
                
                # Add top anchor
                anchor = GSAnchor()
                anchor.name = 'top'
                anchor.position = (0, 0)
                g.anchors.append(anchor)
                
                marks_fixed += 1
                print(f"  Added 'top' anchor to {mark_name}")
                break
    
    print(f"\nTotal marks fixed: {marks_fixed}")
    
    # Save the font
    if output_path is None:
        output_path = glyphs_path
    
    with open(output_path, 'w') as f:
        glyphsLib.writer.dump(font, f)
    print(f"\nSaved to: {output_path}")
    
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_dotted_circle.py <glyphs_file> [output_file]")
        print("Example: python fix_dotted_circle.py sources/HKGroteskBaybayin.glyphs")
        sys.exit(1)
    
    glyphs_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Fixing dotted circle anchors in: {glyphs_path}\n")
    
    success = fix_dotted_circle_anchors(glyphs_path, output_path)
    
    if success:
        print("\n✓ Dotted circle anchors fixed!")
    else:
        print("\n✗ Failed to fix dotted circle anchors")
        sys.exit(1)


if __name__ == "__main__":
    main()