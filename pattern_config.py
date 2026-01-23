"""
Pattern Coloring Configuration
Validated patterns for ages 2-10 with age-appropriate complexity
"""

# Age configuration: count, layout, outline style
AGE_CONFIG = {
    "age_2": {"count": 1, "layout": "in the center of the page", "outline": "Extra thick bold outlines suitable for toddlers"},
    "age_3": {"count": 2, "layout": "side by side", "outline": "Extra thick bold outlines suitable for young children"},
    "age_4": {"count": 4, "layout": "arranged in 2 rows of 2", "outline": "Thick bold outlines"},
    "age_5": {"count": 4, "layout": "arranged in 2 rows of 2", "outline": "Thick bold outlines"},
    "age_6": {"count": 6, "layout": "arranged in 3 rows of 2", "outline": "Thick bold outlines"},
    "age_7": {"count": 6, "layout": "arranged in 3 rows of 2", "outline": "Bold outlines"},
    "age_8": {"count": 6, "layout": "arranged in 3 rows of 2", "outline": "Bold outlines"},
    "age_9": {"count": 6, "layout": "arranged in 3 rows of 2", "outline": "Professional vector art style"},
    "age_10": {"count": 6, "layout": "arranged in 3 rows of 2", "outline": "Professional vector art style"},
}

# Pattern pools by age - validated through extensive testing
PATTERN_POOLS = {
    "age_2": ["horizontal stripes", "polka dots"],  # Pick 1
    "age_3": ["horizontal stripes", "polka dots"],
    "age_4": ["horizontal stripes", "polka dots", "wavy lines", "zigzags"],
    "age_5": ["swirls", "small hearts", "circles", "zigzags"],
    "age_6": ["stripes", "dots", "waves", "zigzags", "hearts", "spirals"],
    "age_7": ["diagonal stripes", "fish scale pattern", "chevron zigzags", "hexagon honeycomb", "bullseye circles", "large polka dots"],
    "age_8": ["diamond grid", "overlapping circles", "herringbone pattern", "teardrop shapes", "leaf pattern", "square grid"],
    "age_9": ["peacock feather scales", "swirling vines", "triangle mosaic", "ocean waves", "sunburst rays", "daisy flowers"],
    "age_10": ["mandala flower", "geometric stars", "paisley teardrops", "celtic knots", "feather pattern", "rose petals"],
}

# Common exclusions for all shapes
BASE_EXCLUSIONS = "people, children, characters, rainbows, clouds, scenery"

# Shape-specific exclusions
SHAPE_EXCLUSIONS = {
    "default": "or decorations",
    "cat": "grass, yarn, or decorations",
    "cats": "grass, yarn, or decorations",
    "dog": "grass, bones, or decorations",
    "dogs": "grass, bones, or decorations",
    "fish": "water, bubbles, seaweed, plants, or decorations",
    "car": "roads, or decorations",
    "cars": "roads, or decorations",
    "truck": "roads, or decorations",
    "trucks": "roads, or decorations",
    "butterfly": "flowers, grass, or decorations",
    "butterflies": "flowers, grass, or decorations",
    "bunny": "carrots, grass, or decorations",
    "bunnies": "carrots, grass, or decorations",
    "easter egg": "grass, bunnies, or decorations",
    "easter eggs": "grass, bunnies, or decorations",
    "mug": "steam, coffee, or decorations",
    "mugs": "steam, coffee, or decorations",
    "star": "or decorations",
    "stars": "or decorations",
    "heart": "or decorations",
    "hearts": "or decorations",
    "flower": "grass, or decorations",
    "flowers": "grass, or decorations",
}


def get_exclusions(shape: str) -> str:
    """Get shape-specific exclusions"""
    shape_lower = shape.lower()
    specific = SHAPE_EXCLUSIONS.get(shape_lower, SHAPE_EXCLUSIONS["default"])
    return f"{BASE_EXCLUSIONS}, {specific}"


def get_plural(shape: str, count: int) -> str:
    """Get plural form of shape"""
    if count == 1:
        return shape
    
    shape_lower = shape.lower()
    
    # Handle irregular plurals
    irregulars = {
        "butterfly": "butterflies",
        "bunny": "bunnies",
        "fish": "fish",
        "sheep": "sheep",
        "mouse": "mice",
        "leaf": "leaves",
    }
    
    if shape_lower in irregulars:
        return irregulars[shape_lower]
    
    # Standard pluralization
    if shape_lower.endswith(('s', 'x', 'z', 'ch', 'sh')):
        return shape + "es"
    elif shape_lower.endswith('y') and shape_lower[-2] not in 'aeiou':
        return shape[:-1] + "ies"
    else:
        return shape + "s"


def generate_pattern_prompt(shape: str, age_level: str) -> str:
    """
    Generate a pattern coloring prompt for any shape at any age level.
    
    Args:
        shape: The item to draw (e.g., "dog", "car", "butterfly")
        age_level: Age level string (e.g., "age_5", "age_10")
    
    Returns:
        Complete prompt string for image generation
    """
    import random
    
    # Get age configuration
    config = AGE_CONFIG.get(age_level, AGE_CONFIG["age_6"])
    count = config["count"]
    layout = config["layout"]
    outline = config["outline"]
    
    # Get patterns for this age
    patterns = PATTERN_POOLS.get(age_level, PATTERN_POOLS["age_6"])
    
    # Get plural form
    plural_shape = get_plural(shape, count)
    
    # Build pattern descriptions
    if count == 1:
        # Single shape - pick one pattern
        pattern = random.choice(patterns)
        pattern_desc = f"The {shape} has {pattern} on its body."
    else:
        # Multiple shapes - assign different patterns
        selected_patterns = random.sample(patterns, min(count, len(patterns)))
        
        # If we need more patterns than available, repeat some
        while len(selected_patterns) < count:
            selected_patterns.append(random.choice(patterns))
        
        pattern_desc = " ".join([
            f"One {shape} has {p}." for p in selected_patterns
        ])
    
    # Get exclusions
    exclusions = get_exclusions(shape)
    
    # Build the prompt
    if count == 1:
        prompt = f"""CRITICAL: This image MUST contain ONLY 1 {shape} and NOTHING else. 1 very large simple cartoon {shape} {layout}. {pattern_desc} Very simple shapes. {outline}. Professional vector art style with clean connected lines. IMPORTANT: Do NOT add any {exclusions}. The background MUST be pure white. ONLY the 1 large patterned {shape}."""
    else:
        prompt = f"""CRITICAL: This image MUST contain ONLY {count} {plural_shape} and NOTHING else. {count} cartoon {plural_shape} {layout}. {pattern_desc} Very simple shapes. {outline}. Professional vector art style with clean connected lines. IMPORTANT: Do NOT add any {exclusions}. The background MUST be pure white. ONLY the {count} patterned {plural_shape}."""
    
    return prompt


def generate_pattern_prompt_deterministic(shape: str, age_level: str, pattern_index: int = 0) -> str:
    """
    Generate a pattern coloring prompt with deterministic pattern selection.
    Useful for consistent results or cycling through patterns.
    
    Args:
        shape: The item to draw
        age_level: Age level string
        pattern_index: Starting index for pattern selection (for consistency)
    
    Returns:
        Complete prompt string for image generation
    """
    # Get age configuration
    config = AGE_CONFIG.get(age_level, AGE_CONFIG["age_6"])
    count = config["count"]
    layout = config["layout"]
    outline = config["outline"]
    
    # Get patterns for this age
    patterns = PATTERN_POOLS.get(age_level, PATTERN_POOLS["age_6"])
    
    # Get plural form
    plural_shape = get_plural(shape, count)
    
    # Build pattern descriptions deterministically
    if count == 1:
        pattern = patterns[pattern_index % len(patterns)]
        pattern_desc = f"The {shape} has {pattern} on its body."
    else:
        selected_patterns = []
        for i in range(count):
            idx = (pattern_index + i) % len(patterns)
            selected_patterns.append(patterns[idx])
        
        pattern_desc = " ".join([
            f"One {shape} has {p}." for p in selected_patterns
        ])
    
    # Get exclusions
    exclusions = get_exclusions(shape)
    
    # Build the prompt
    if count == 1:
        prompt = f"""CRITICAL: This image MUST contain ONLY 1 {shape} and NOTHING else. 1 very large simple cartoon {shape} {layout}. {pattern_desc} Very simple shapes. {outline}. Professional vector art style with clean connected lines. IMPORTANT: Do NOT add any {exclusions}. The background MUST be pure white. ONLY the 1 large patterned {shape}."""
    else:
        prompt = f"""CRITICAL: This image MUST contain ONLY {count} {plural_shape} and NOTHING else. {count} cartoon {plural_shape} {layout}. {pattern_desc} Very simple shapes. {outline}. Professional vector art style with clean connected lines. IMPORTANT: Do NOT add any {exclusions}. The background MUST be pure white. ONLY the {count} patterned {plural_shape}."""
    
    return prompt


# Example usage and testing
if __name__ == "__main__":
    # Test various shapes and ages
    test_cases = [
        ("dog", "age_2"),
        ("cat", "age_3"),
        ("butterfly", "age_5"),
        ("truck", "age_7"),
        ("heart", "age_10"),
    ]
    
    print("=" * 80)
    print("PATTERN COLORING PROMPT GENERATOR - TEST OUTPUT")
    print("=" * 80)
    
    for shape, age in test_cases:
        print(f"\n### {shape.upper()} - {age.upper()} ###")
        print("-" * 60)
        prompt = generate_pattern_prompt(shape, age)
        print(prompt)
        print()
