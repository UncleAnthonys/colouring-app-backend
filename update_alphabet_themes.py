import json

# Load existing themes
with open('prompts/themes.json', 'r') as f:
    data = json.load(f)

# Alphabet items for each letter
alphabet_items = {
    'a': {'costume': 'astronaut', 'objects': 'apple, airplane, ant, alligator, anchor, arrow'},
    'b': {'costume': 'builder or ballerina', 'objects': 'ball, balloon, butterfly, bear, banana, bird'},
    'c': {'costume': 'cowboy or chef', 'objects': 'cat, car, cake, cow, castle, cupcake'},
    'd': {'costume': 'doctor or dinosaur onesie', 'objects': 'dog, duck, dolphin, donut, drum, dinosaur'},
    'e': {'costume': 'explorer with hat', 'objects': 'elephant, egg, envelope, earth, eagle'},
    'f': {'costume': 'firefighter or fairy', 'objects': 'fish, frog, flower, fox, flag, feather'},
    'g': {'costume': 'gardener or ghost', 'objects': 'giraffe, grapes, guitar, goat, gift, glasses'},
    'h': {'costume': 'superhero or witch with hat', 'objects': 'horse, heart, house, helicopter, hippo, hat'},
    'i': {'costume': 'ice skater', 'objects': 'ice cream, igloo, iguana, insect, island'},
    'j': {'costume': 'jester or judge', 'objects': 'jellyfish, jam, jet, jigsaw, juice, jump rope'},
    'k': {'costume': 'king or knight', 'objects': 'kite, kitten, key, kangaroo, koala, kettle'},
    'l': {'costume': 'lion tamer or ladybug outfit', 'objects': 'lion, leaf, lemon, ladybug, lamp, lollipop'},
    'm': {'costume': 'magician or mermaid', 'objects': 'monkey, moon, mushroom, mouse, muffin, milk'},
    'n': {'costume': 'ninja or nurse', 'objects': 'nest, nut, noodles, narwhal, newspaper, night sky'},
    'o': {'costume': 'astronaut (space)', 'objects': 'owl, octopus, orange, otter, onion, ocean'},
    'p': {'costume': 'pirate or princess', 'objects': 'pig, penguin, pizza, pumpkin, parrot, pear'},
    'q': {'costume': 'queen', 'objects': 'queen, quilt, question mark, quail, quarter'},
    'r': {'costume': 'robot or race car driver', 'objects': 'rabbit, rainbow, rocket, rose, robot, rain'},
    's': {'costume': 'superhero or sailor', 'objects': 'sun, star, snake, strawberry, snail, sheep'},
    't': {'costume': 'train conductor or tiger onesie', 'objects': 'tiger, tree, train, turtle, tomato, tent'},
    'u': {'costume': 'unicorn onesie', 'objects': 'umbrella, unicorn, ukulele, uniform'},
    'v': {'costume': 'viking or vet', 'objects': 'violin, volcano, van, vegetables, vase, vest'},
    'w': {'costume': 'wizard or witch', 'objects': 'whale, watermelon, worm, wagon, watch, window'},
    'x': {'costume': 'superhero with X', 'objects': 'x-ray, xylophone, x marks the spot, fox, box'},
    'y': {'costume': 'yak onesie', 'objects': 'yo-yo, yak, yogurt, yarn, yacht'},
    'z': {'costume': 'zookeeper or zebra onesie', 'objects': 'zebra, zoo, zipper, zero, zeppelin'},
}

def create_alphabet_overlay(letter, items):
    letter_upper = letter.upper()
    return f"""DRAW:
- 1-2 cute children wearing simple COSTUMES that start with {letter_upper} (e.g. {items['costume']} outfit)
- A big friendly letter {letter_upper} CHARACTER with a cute face, arms and legs
- 3-4 objects that start with {letter_upper} ({items['objects']})

IMPORTANT: Do NOT put the letter {letter_upper} printed on clothing - dress them in themed COSTUMES instead

The letter {letter_upper} must be LARGE and clearly visible as a friendly character.

NO TEXT - do not write any words or labels, only the letter {letter_upper} as a character."""

# Update all alphabet themes
for letter in 'abcdefghijklmnopqrstuvwxyz':
    theme_key = f'alphabet_{letter}'
    if theme_key in data['themes']:
        items = alphabet_items[letter]
        data['themes'][theme_key]['overlay'] = create_alphabet_overlay(letter, items)
        data['themes'][theme_key]['text_only'] = True
        print(f"Updated {theme_key}")

# Save updated themes
with open('prompts/themes.json', 'w') as f:
    json.dump(data, f, indent=2)

print("\n✅ All 26 alphabet themes updated!")
print("\nExample (alphabet_a):")
print(data['themes']['alphabet_a']['overlay'])
