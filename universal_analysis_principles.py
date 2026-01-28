universal_prompt = """
Analyze this child's drawing using these visual analysis principles:

1. **FLOW vs SPIKY**: Distinguish between:
   - Long flowing elements (hair, fabric, etc.) that extend significant distances
   - Short spiky elements (decorative features, texture, etc.)

2. **PROPORTIONAL CONTEXT**: 
   - If strokes extend >50% of the figure's height, they're likely long/flowing
   - Compare element sizes relative to the whole figure

3. **CLOTHING vs BODY**:
   - Segmented horizontal sections usually indicate clothing/dress
   - Solid areas usually indicate body parts

4. **SEQUENTIAL MAPPING**: 
   - Record exact order of colors/elements from top to bottom
   - Note specific proportions and relationships

Apply these principles to describe the character's features accurately.
"""

print("Universal principles for any character drawing:")
print(universal_prompt)
