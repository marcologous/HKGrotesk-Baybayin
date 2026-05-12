#!/usr/bin/env python3
"""
Build script for HKGrotesk-Baybayin font.
Generates TTFs from Glyphs sources with proper fixes for Google Fonts submission.
"""

import os
import sys
import shutil
import subprocess
import glyphsLib
from glyphsLib.classes import GSFont, GSAnchor, GSGlyph, GSLayer, GSPath, GSNode


# Configuration
SOURCES_DIR = "sources"
FONTS_DIR = "fonts"
INSTANCE_DIR = "instance_ttf"

# Font family name (change from HK to Hanken)
FAMILY_NAME = "Hanken Grotesk Baybayin"

# Copyright string (with URL for Fontbakery)
COPYRIGHT = "Copyright 2024 The Hanken Grotesk Baybayin Project Authors (https://github.com/marcologous/hkgrotesk-baybayin)"


def fix_font_metadata(glyphs_path):
    """Fix font metadata: rename family, fix copyright, add dotted circle."""
    
    print(f"Fixing metadata in: {glyphs_path}")
    
    font = glyphsLib.load(glyphs_path)
    
    # 1. Rename family name (HK -> Hanken)
    old_name = font.familyName
    font.familyName = FAMILY_NAME
    print(f"  Family: {old_name} -> {FAMILY_NAME}")
    
    # 2. Fix copyright (remove email)
    font.copyright = COPYRIGHT
    print(f"  Copyright: {COPYRIGHT}")
    
    # 3. Dotted circle will be added by DottedCircleFilter during build
    # No need to create it manually
    print("  Dotted circle will be added by DottedCircleFilter")
    
    # Save
    with open(glyphs_path, 'w') as f:
        glyphsLib.writer.dump(font, f)
    
    print(f"  Saved: {glyphs_path}\n")


def build_fonts():
    """Build all font files from Glyphs sources."""
    
    # Clean up
    if os.path.exists(INSTANCE_DIR):
        shutil.rmtree(INSTANCE_DIR)
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    
    # Fix metadata in both sources
    upright_path = os.path.join(SOURCES_DIR, "HKGroteskBaybayin.glyphs")
    italic_path = os.path.join(SOURCES_DIR, "HKGroteskBaybayinItalic.glyphs")
    
    fix_font_metadata(upright_path)
    fix_font_metadata(italic_path)
    
    # Build upright fonts
    print("Building upright fonts...")
    cmd = [
        "fontmake",
        "-g", upright_path,
        "-o", "ttf",
        "-i",
        "--filter", "DottedCircleFilter(pre=True)",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        sys.exit(1)
    
    # Build italic fonts
    print("Building italic fonts...")
    cmd = [
        "fontmake",
        "-g", italic_path,
        "-o", "ttf",
        "-i",
        "--filter", "DottedCircleFilter(pre=True)",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        sys.exit(1)
    
    # Move to fonts directory
    print("Moving fonts to fonts directory...")
    for f in os.listdir(INSTANCE_DIR):
        if f.endswith('.ttf'):
            src = os.path.join(INSTANCE_DIR, f)
            dst = os.path.join(FONTS_DIR, f)
            shutil.move(src, dst)
            print(f"  {f}")
    
    # Run ttfautohint on all fonts (or use gftools as fallback)
    print("\nRunning hinting...")
    
    # Check if ttfautohint is available
    ttfautohint_available = shutil.which('ttfautohint') is not None
    gftools_available = shutil.which('gftools') is not None
    
    if ttfautohint_available:
        for f in os.listdir(FONTS_DIR):
            if f.endswith('.ttf'):
                font_path = os.path.join(FONTS_DIR, f)
                # Create backup
                backup_path = font_path + '.bak'
                shutil.copy(font_path, backup_path)
                
                # Run ttfautohint
                result = subprocess.run(
                    ['ttfautohint', font_path, font_path],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print(f"  WARNING: ttfautohint failed for {f}")
                    # Restore backup
                    shutil.move(backup_path, font_path)
                else:
                    os.remove(backup_path)
                    print(f"  {f} (ttfautohint)")
    elif gftools_available:
        # Try gftools fix-nonhinting
        print("  ttfautohint not found, using gftools...")
        for f in os.listdir(FONTS_DIR):
            if f.endswith('.ttf'):
                font_path = os.path.join(FONTS_DIR, f)
                result = subprocess.run(
                    ['gftools', 'fix-nonhinting', font_path],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"  {f} (gftools)")
                else:
                    print(f"  WARNING: gftools failed for {f}")
    else:
        print("  SKIPPED: ttfautohint and gftools not available")
        print("  Install with: brew install ttfautohint && pip install gftools")
    
    # Copy OFL.txt to fonts directory
    ofl_src = "OFL.txt"
    ofl_dst = os.path.join(FONTS_DIR, "OFL.txt")
    if os.path.exists(ofl_src):
        shutil.copy(ofl_src, ofl_dst)
        print(f"\nCopied OFL.txt to fonts/")
    
    # Fix name table entries
    fix_name_table()
    
    print("\n✓ Build complete!")


def fix_name_table():
    """Fix name table entries in all built fonts."""
    
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.tables._g_a_s_p import table__g_a_s_p
    
    print("\nFixing name table and gasp table...")
    
    for f in os.listdir(FONTS_DIR):
        if f.endswith('.ttf'):
            font_path = os.path.join(FONTS_DIR, f)
            font = TTFont(font_path)
            
            # Fix copyright (name ID 0)
            for record in font['name'].names:
                if record.nameID == 0:
                    record.string = COPYRIGHT
            
            # Fix family name (name ID 1) if needed
            for record in font['name'].names:
                if record.nameID == 1:
                    # Update to match new family name
                    if 'HK Grotesk' in record.toUnicode():
                        record.string = FAMILY_NAME
            
            # Add gasp table if not present
            from fontTools.ttLib.tables._g_a_s_p import table__g_a_s_p
            if 'gasp' not in font:
                gasp = table__g_a_s_p()
                gasp.version = 1
                gasp.gaspRange = {}
                # Set gasp range for all pixel sizes
                # 0xFFFF means "all other sizes"
                gasp.gaspRange[0xFFFF] = 0x000F  # grid-fitting and smoothing
                font['gasp'] = gasp
            
            font.save(font_path)
            print(f"  Fixed: {f}")


def run_fontbakery():
    """Run Fontbakery check on Regular font."""
    
    regular = os.path.join(FONTS_DIR, "HankenGroteskBaybayin-Regular.ttf")
    if not os.path.exists(regular):
        print("ERROR: Regular font not found!")
        return
    
    print("\nRunning Fontbakery...")
    result = subprocess.run(
        ["fontbakery", "check-googlefonts", regular],
        capture_output=True,
        text=True
    )
    
    # Parse results
    lines = result.stdout.split('\n')
    for line in lines:
        if any(x in line for x in ["FAIL:", "WARN:", "PASS:", "Total:"]):
            print(line)
    
    # Show failures
    print("\n--- FAILs ---")
    in_fail = False
    for line in lines:
        if "FAIL:" in line:
            in_fail = True
        if in_fail:
            print(line)
            if "Result: FAIL" in line:
                in_fail = False


def main():
    print("=" * 60)
    print("HKGrotesk Baybayin Font Builder")
    print("=" * 60 + "\n")
    
    build_fonts()
    run_fontbakery()


if __name__ == "__main__":
    main()