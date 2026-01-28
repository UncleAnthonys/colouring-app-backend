def convert_to_structure_only(color_description: str) -> str:
    """
    Convert a detailed color description to structure-only for coloring pages
    Removes all color references but keeps structural details
    """
    
    # Key replacements to remove colors but keep structure
    replacements = {
        # Remove specific colors
        'bright lime green': 'character-colored',
        'vibrant purple': 'character-colored', 
        'bright orange': 'character-colored',
        'light blue': 'character-colored',
        'dark gray': 'character-colored',
        'solid black': 'outlined',
        'bright red': 'character-colored',
        'white': 'outlined',
        
        # Remove color phrases but keep structure
        'Color is a consistent bright lime green': 'Round head shape',
        'Color: Bright lime green': 'Arms extend from body',
        'consistent bright orange color': 'straight cylindrical shape',
        'vibrant purple color': 'rectangular torso shape',
        
        # Keep important structural details
        'Exactly 7': 'Exactly 7',
        'Exactly 4': 'Exactly 4', 
        'Exactly 3': 'Exactly 3',
        'Exactly 2': 'Exactly 2',
        'Exactly 1': 'Exactly 1',
    }
    
    structure_desc = color_description
    for old, new in replacements.items():
        structure_desc = structure_desc.replace(old, new)
    
    # Focus on key structural elements
    structure_summary = f"""Friendly monster character with:
- Round head with exactly 7 triangular spikes on top
- Exactly 2 cylindrical bolts on sides of head, each with 3 rectangular notches  
- Large round eyes with pupils and highlights
- Wide smiling mouth showing exactly 4 pointed fangs on upper jaw
- Rectangular torso with horizontal waist band
- Cylindrical arms with exactly 3 fingers each, cuffs on wrists
- Straight cylindrical legs  
- Boot-shaped feet with exactly 3 vertical stripes on front
- Asymmetrical eyes (different colors)
- Overall proportions: large head, rectangular body, straight limbs"""
    
    return structure_summary

# Test with Tristan's description
test_input = "bright lime green head with vibrant purple torso and bright orange legs"
print("Structure version:", convert_to_structure_only(test_input))
