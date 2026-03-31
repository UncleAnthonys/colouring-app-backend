"""
Region Map Generator for Little Lines Colouring Pages
=====================================================
Uses OpenCV to detect black outlines and segment the image into
individually-labelled regions. The output is a region map PNG where
each enclosed area has a unique colour ID.

Used by the ColourOnScreen widget for:
1. "Stay in the lines" masking
2. Tap-to-fill (future)
3. Colour by numbers (future)

Usage:
    from region_map import generate_region_map
    
    # From file bytes (e.g. after generating a colouring page)
    region_map_bytes, num_regions = generate_region_map(image_bytes)
    
    # Returns: (PNG bytes of region map, number of regions found)
"""

import cv2
import numpy as np
from io import BytesIO


def generate_region_map(
    image_bytes: bytes,
    line_threshold: int = 180,
    min_region_size: int = 100,
    line_thickness_dilate: int = 2,
) -> tuple[bytes, int]:
    """
    Generate a region map from a colouring page image.
    
    Args:
        image_bytes: Raw PNG/JPEG bytes of the colouring page
        line_threshold: Pixels darker than this (0-255) are treated as lines.
                       Higher = more aggressive line detection. Default 180.
        min_region_size: Minimum pixel count for a region to be kept.
                        Smaller regions get merged into neighbours. Default 100.
        line_thickness_dilate: How many pixels to dilate (thicken) lines by.
                              Helps close small gaps in AI-generated lines.
                              Default 2.
    
    Returns:
        Tuple of (region_map_png_bytes, num_regions)
        - region_map_png_bytes: PNG where each region has a unique colour
          R channel = region_id % 256
          G channel = (region_id // 256) % 256  
          B channel = 255 (fully opaque marker)
          A channel = 255 for regions, 0 for lines
          This encoding supports up to 65,536 unique regions.
        - num_regions: Number of regions found (excluding background/lines)
    """
    # Decode image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        raise ValueError("Could not decode image")
    
    h, w = img.shape
    
    # Step 1: Create binary mask of lines vs colourable areas
    # Threshold: pixels below line_threshold are lines (black), above are white
    _, binary = cv2.threshold(img, line_threshold, 255, cv2.THRESH_BINARY)
    
    # Step 2: Dilate the lines slightly to close small gaps
    # This is crucial for AI-generated images which often have hairline gaps
    if line_thickness_dilate > 0:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, 
            (line_thickness_dilate * 2 + 1, line_thickness_dilate * 2 + 1)
        )
        # Invert (lines become white), dilate (thicken lines), invert back
        inverted = cv2.bitwise_not(binary)
        dilated = cv2.dilate(inverted, kernel, iterations=1)
        binary = cv2.bitwise_not(dilated)
    
    # Step 3: Find connected components (each white region gets a unique label)
    num_labels, labels = cv2.connectedComponents(binary, connectivity=8)
    
    # Step 4: Filter out tiny regions (noise, stray pixels)
    # Count pixels per region
    region_sizes = np.bincount(labels.flatten())
    
    # Map small regions to their nearest large neighbour
    small_regions = set()
    for label_id in range(1, num_labels):  # Skip 0 (background/lines)
        if region_sizes[label_id] < min_region_size:
            small_regions.add(label_id)
    
    if small_regions:
        # For each small region, find the nearest large region and merge
        for label_id in small_regions:
            # Find pixels of this small region
            ys, xs = np.where(labels == label_id)
            if len(ys) == 0:
                continue
            
            # Check neighbours of the region's bounding box
            min_y, max_y = max(0, ys.min() - 3), min(h, ys.max() + 4)
            min_x, max_x = max(0, xs.min() - 3), min(w, xs.max() + 4)
            
            neighbourhood = labels[min_y:max_y, min_x:max_x]
            neighbour_labels = np.unique(neighbourhood)
            
            # Find the largest neighbouring region that isn't this one or lines
            best_neighbour = 0
            best_size = 0
            for nl in neighbour_labels:
                if nl == label_id or nl == 0 or nl in small_regions:
                    continue
                if region_sizes[nl] > best_size:
                    best_size = region_sizes[nl]
                    best_neighbour = nl
            
            if best_neighbour > 0:
                labels[labels == label_id] = best_neighbour
    
    # Step 5: Re-number regions to be contiguous (1, 2, 3, ...)
    unique_labels = np.unique(labels)
    unique_labels = unique_labels[unique_labels != 0]  # Remove background
    
    remap = np.zeros(labels.max() + 1, dtype=np.int32)
    for new_id, old_id in enumerate(unique_labels, start=1):
        remap[old_id] = new_id
    
    labels = remap[labels]
    num_regions = len(unique_labels)
    
    # Step 6: Encode as RGBA PNG
    # R = region_id % 256
    # G = (region_id // 256) % 256
    # B = 255 (marker that this is a valid region)
    # A = 255 for regions, 0 for lines/background
    region_map = np.zeros((h, w, 4), dtype=np.uint8)
    
    # Lines/background (label 0) stay fully transparent
    mask = labels > 0
    region_map[mask, 0] = (labels[mask] % 256).astype(np.uint8)
    region_map[mask, 1] = ((labels[mask] // 256) % 256).astype(np.uint8)
    region_map[mask, 2] = 255  # Marker
    region_map[mask, 3] = 255  # Opaque
    
    # Encode to PNG
    success, png_bytes = cv2.imencode('.png', region_map)
    if not success:
        raise ValueError("Could not encode region map to PNG")
    
    return png_bytes.tobytes(), num_regions


def generate_boundary_mask(image_bytes: bytes, line_threshold: int = 220) -> bytes:
    """
    Generate a simple boundary mask (white where colourable, transparent where lines).
    This is the simpler version used by the Flutter widget for "stay in the lines".
    
    Args:
        image_bytes: Raw PNG/JPEG bytes of the colouring page
        line_threshold: Pixels darker than this are treated as lines.
    
    Returns:
        PNG bytes of mask (white+opaque = colourable, transparent = lines)
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        raise ValueError("Could not decode image")
    
    h, w = img.shape
    
    # Threshold
    _, binary = cv2.threshold(img, line_threshold, 255, cv2.THRESH_BINARY)
    
    # Slight erosion to make lines a bit thicker (better masking)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    inverted = cv2.bitwise_not(binary)
    dilated = cv2.dilate(inverted, kernel, iterations=2)
    binary = cv2.bitwise_not(dilated)
    
    # Build RGBA: white+opaque where colourable, transparent where lines
    mask = np.zeros((h, w, 4), dtype=np.uint8)
    colourable = binary == 255
    mask[colourable, 0] = 255
    mask[colourable, 1] = 255
    mask[colourable, 2] = 255
    mask[colourable, 3] = 255
    # Lines stay (0, 0, 0, 0) = transparent
    
    success, png_bytes = cv2.imencode('.png', mask)
    if not success:
        raise ValueError("Could not encode mask to PNG")
    
    return png_bytes.tobytes()


if __name__ == "__main__":
    """Quick test: run on a local image file"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python region_map.py <image_path>")
        sys.exit(1)
    
    with open(sys.argv[1], "rb") as f:
        img_bytes = f.read()
    
    # Generate region map
    region_map_bytes, num_regions = generate_region_map(img_bytes)
    
    output_path = sys.argv[1].rsplit(".", 1)[0] + "_regionmap.png"
    with open(output_path, "wb") as f:
        f.write(region_map_bytes)
    
    print(f"✅ Found {num_regions} regions")
    print(f"✅ Region map saved to {output_path}")
    
    # Also generate simple mask
    mask_bytes = generate_boundary_mask(img_bytes)
    
    mask_path = sys.argv[1].rsplit(".", 1)[0] + "_mask.png"
    with open(mask_path, "wb") as f:
        f.write(mask_bytes)
    
    print(f"✅ Boundary mask saved to {mask_path}")
