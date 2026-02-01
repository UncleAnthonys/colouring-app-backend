# Little Lines - Adventure Story API Documentation

## Overview
The Adventure Story API transforms children's drawings into personalized coloring story books. A child draws a character, the API creates a Pixar-style 3D reveal, generates personalized stories based on the character's unique features, and produces coloring pages with age-appropriate story text.

**Base URL:** `https://colouring-app-api.onrender.com`  
**All adventure endpoints are prefixed with:** `/adventure`

---

## Complete Flow
```
1. UPLOAD DRAWING → Extract & Reveal
2. REVEAL PAGE → Show reveal + 3 story options with blurbs
3. USER SELECTS STORY → Generate front cover
4. GENERATE EPISODES → Coloring pages with story text (A4 format)
```

---

## Step 1: Extract & Reveal Character

**`POST /adventure/extract-and-reveal`**

Analyzes a child's drawing and generates a Pixar-style 3D character reveal.

### Request
- **Content-Type:** `multipart/form-data`
- **Fields:**
  - `image` (file, required): The child's drawing image (JPG, PNG, WEBP)
  - `character_name` (string, required): Name the child gave the character

### Response
```json
{
  "character": {
    "name": "Sparkle",
    "description": "Full character analysis text (used for story generation)...",
    "key_feature": "Distinctive features from original drawing"
  },
  "reveal_description": "Full detailed analysis (same as character.description)",
  "reveal_image": "base64_encoded_png_image",
  "extraction_time": 0,
  "model_used": "gemini-2.5-flash"
}
```

### Key Fields to Store
| Field | Use |
|-------|-----|
| `character` | Pass to all subsequent endpoints |
| `character.description` | Pass as `character_description` to story generation |
| `reveal_image` | Display as the character reveal, pass as `reveal_image_b64` to episode/cover generation |

### FlutterFlow Integration
- **Type:** API Call with file upload
- Store entire `character` object as Page State (JSON)
- Store `reveal_image` as Page State (String) for display and later use
- Display reveal image: decode base64 to image widget

---

## Step 2: Generate Story Options

**`POST /adventure/generate-stories`**

Generates 3 personalized story themes based on the character's unique features, each with 10 episodes.

### Request
```json
{
  "character_name": "Sparkle",
  "character_description": "Full description from Step 1 character.description",
  "age_level": "age_7"
}
```

### Age Levels
| Value | Age | Writing Style |
|-------|-----|---------------|
| `age_3` | 2-3 years | Rhyming, repetitive, soothing rhythm |
| `age_4` | 4 years | Playful rhymes, fun sounds (pitter-patter) |
| `age_5` | 5 years | Silly words (super-duper, teeny-tiny), giggles |
| `age_6` | 6 years | Vivid comparisons, expressive dialogue |
| `age_7` | 7 years | Action words, cheeky humor, puns |
| `age_8` | 8 years | Witty wordplay, dramatic vocabulary |
| `age_9` | 9 years | Sophisticated observations, emotional depth |
| `age_10` | 10+ years | Literary quality, metaphors, mature wit |

### Response
```json
{
  "character_name": "Sparkle",
  "age_level": "age_7",
  "themes": [
    {
      "theme_id": "the_lucky_clover_charm",
      "theme_name": "The Lucky Clover Charm",
      "theme_description": "Sparkle discovers her special clover brings unexpected good fortune.",
      "theme_blurb": "Sparkle discovers her special clover brings unexpected good fortune on exciting expeditions.",
      "episodes": [
        {
          "episode_num": 1,
          "title": "A Whispering Wind's Map",
          "scene_description": "Sparkle standing in a meadow with a mysterious map floating in the breeze...",
          "story_text": "A whispering wind carried a crinkled old map right to Sparkle's feet..."
        }
        // ... 10 episodes total
      ]
    }
    // ... 3 themes total
  ]
}
```

### Key Fields for UI
| Field | Use |
|-------|-----|
| `theme_name` | Display as story title |
| `theme_blurb` | Display under title to help user choose (1 exciting sentence) |
| `theme_description` | Pass to front cover generation |
| `episodes[].title` | Episode title for A4 page |
| `episodes[].scene_description` | Pass to episode generation |
| `episodes[].story_text` | Story text displayed under coloring image on A4 page |

### FlutterFlow Integration
- Store full response as App State or Page State (JSON)
- Display 3 theme cards on reveal page, each showing:
  - `theme_name` as title
  - `theme_blurb` as subtitle/description
- On theme selection, store selected theme index

---

## Step 3: Generate Front Cover

**`POST /adventure/generate/front-cover`**

Generates a coloring book front cover with the story title and character.

### Request
```json
{
  "character": {
    "name": "Sparkle",
    "description": "Full character description...",
    "key_feature": "Distinctive features..."
  },
  "theme_name": "The Lucky Clover Charm",
  "theme_description": "Sparkle discovers her special clover brings unexpected good fortune.",
  "age_level": "age_7",
  "reveal_image_b64": "base64_reveal_image_from_step_1"
}
```

### Response
```json
{
  "cover_image_b64": "base64_encoded_png",
  "cover_page_b64": "base64_encoded_png",
  "title": "Sparkle and The Lucky Clover Charm"
}
```

### Notes
- `cover_image_b64` and `cover_page_b64` are the same image (Gemini generates full cover with text)
- Cover includes title text rendered by Gemini in hand-drawn style
- Cover is black and white line art, suitable for coloring

### FlutterFlow Integration
- Call when user selects a theme
- Display as first page of the story book
- Store `cover_page_b64` for PDF generation

---

## Step 4: Generate Episode Pages

**`POST /adventure/generate/episode-gemini`**

Generates a single episode coloring page with A4 formatted output including title and story text.

### Request
```json
{
  "character": {
    "name": "Sparkle",
    "description": "Full character description...",
    "key_feature": "Distinctive features..."
  },
  "theme": "The Lucky Clover Charm",
  "episode_num": 1,
  "age_level": "age_7",
  "reveal_image_b64": "base64_reveal_image_from_step_1",
  "scene_prompt": "Sparkle standing in a meadow with a mysterious map...",
  "story_text": "A whispering wind carried a crinkled old map...",
  "episode_title": "A Whispering Wind's Map"
}
```

### Where Request Fields Come From
| Field | Source |
|-------|--------|
| `character` | Step 1 response `character` object |
| `theme` | Step 2 selected `theme_name` |
| `episode_num` | Step 2 selected episode `episode_num` |
| `age_level` | User's selected age |
| `reveal_image_b64` | Step 1 response `reveal_image` |
| `scene_prompt` | Step 2 selected episode `scene_description` |
| `story_text` | Step 2 selected episode `story_text` |
| `episode_title` | Step 2 selected episode `title` |

### Response
```json
{
  "image_b64": "base64_coloring_image_only",
  "page_b64": "base64_full_a4_page_with_title_and_story",
  "story": "The story text used on the page",
  "episode_num": 1,
  "title": "A Whispering Wind's Map",
  "is_choice_point": false,
  "choices": null,
  "choice_prompt": null
}
```

### Key Fields
| Field | Use |
|-------|-----|
| `image_b64` | Just the coloring image (for thumbnails/previews) |
| `page_b64` | **Full A4 page** with coloring image + title + story text underneath (for display/print) |
| `title` | Episode title |
| `story` | Story text shown on page |

### A4 Page Layout
```
┌─────────────────────────┐
│      (small margin)      │
│  ┌───────────────────┐  │
│  │                   │  │
│  │                   │  │
│  │   COLORING IMAGE  │  │
│  │     (82% height)  │  │
│  │                   │  │
│  │                   │  │
│  └───────────────────┘  │
│                          │
│     Episode Title        │
│   Story text centered    │
│   below the image...     │
└─────────────────────────┘
```

### FlutterFlow Integration
- Call for each episode the user wants to generate
- Can generate episodes on-demand (not all 10 at once)
- Display `page_b64` as the main view
- Store for PDF compilation

---

## Complete FlutterFlow Flow

### Page 1: Drawing Upload
```
1. User draws character on paper
2. User takes photo / uploads image
3. User types character name
4. Call POST /adventure/extract-and-reveal
5. Navigate to Reveal Page
```

### Page 2: Character Reveal + Story Selection
```
1. Display reveal_image (decoded from base64)
2. Display 3 story option cards:
   ┌─────────────────────────┐
   │ 📖 [theme_name]         │
   │ [theme_blurb]           │
   │         [Select Button] │
   └─────────────────────────┘
3. User taps a story → Navigate to Story Page
```

### Page 3: Story Book
```
1. Call POST /adventure/generate/front-cover
2. Display front cover as Page 1
3. For each episode (on-demand or batch):
   a. Call POST /adventure/generate/episode-gemini
   b. Display page_b64 as next page
4. User swipes through pages like a book
```

### Data to Pass Between Pages
| From → To | Data |
|-----------|------|
| Upload → Reveal | `character` (JSON), `reveal_image` (String), `reveal_description` (String) |
| Reveal → Story | Above + selected `theme` (JSON), `age_level` (String) |

### Page State Variables (Reveal Page)
| Variable | Type | Is List | Nullable |
|----------|------|---------|----------|
| character | JSON | unchecked | unchecked |
| revealImage | String | unchecked | unchecked |
| storyThemes | JSON | checked | unchecked |
| selectedAge | String | unchecked | unchecked |

### Page State Variables (Story Page)
| Variable | Type | Is List | Nullable |
|----------|------|---------|----------|
| character | JSON | unchecked | unchecked |
| revealImage | String | unchecked | unchecked |
| selectedTheme | JSON | unchecked | unchecked |
| ageLevel | String | unchecked | unchecked |
| currentEpisode | int | unchecked | unchecked |
| coverImage | String | unchecked | checked |
| episodePages | String | checked | unchecked |

---

## Story Personalization Features

### Feature-Driven Stories
Stories are built around the character's most interesting features:
- **Priority 1:** Unusual body parts (multiple eyes, extra arms, wings, tails)
- **Priority 2:** Special accessories (horns, crown, wand)
- **Priority 3:** Other unique features

Each of the 3 themes focuses on a DIFFERENT unique feature.

### No Specific Body Part Numbers
Stories never mention exact counts for body parts (e.g., never "8 eyes" or "6 arms") because AI counting is unreliable. Instead uses creative descriptions:
- "lots of eyes scanning everywhere"
- "extra arms juggling everything at once"
- "all those helpful hands"

### Age-Appropriate Writing Styles
| Age | Style |
|-----|-------|
| 3-4 | Rhyming, repetition, fun sounds |
| 5-6 | Silly words, giggles, vivid comparisons |
| 7-8 | Action words, puns, cheeky humor |
| 9-10 | Sophisticated vocabulary, emotional depth, literary quality |

---

## Backend Files Reference

| File | Purpose |
|------|---------|
| `adventure_endpoints.py` | FastAPI endpoints and request/response models |
| `adventure_gemini.py` | Gemini AI functions: reveal gen, episode gen, story gen, A4 page creation, front cover |
| `adventure_config.py` | Age rules for coloring page complexity |
| `character_extraction_gemini.py` | Character analysis from drawings |

---

## API Base URL & Repository

- **Live API:** https://colouring-app-api.onrender.com
- **GitHub:** https://github.com/UncleAnthonys/colouring-app-backend
- **Endpoints prefix:** All adventure endpoints use `/adventure/` prefix
