import json
import re

# JSON Path
input_file_path = 'weeknd/weeknd_all_dirty.json'
output_file_path = 'weeknd/weeknd_all_clean_fr.json'

# The unwanted string to be removed
unwanted_string = "\nYou might also like"
# Pattern to match encoding information at the end of lyrics
# Assumes the encoding information always starts with a digit followed by "Embed"
# encoding_pattern = re.compile(r'\d+You might also like$')
# encoding_pattern = re.compile(r'(\w+)\[151You might also like\]')
encoding_pattern = re.compile(r'\d+Embed$')


def cleanse_lyrics(input_path, output_path, unwanted_str, encoding_re):
    # Read the JSON data from the file
    with open(input_path, 'r', encoding='utf-8') as file:
        songs = json.load(file)
    
    # Iterate over each song
    for song in songs:
        # Remove the specific unwanted string if present
        if unwanted_str in song['lyrics']:
            song['lyrics'] = song['lyrics'].replace(unwanted_str, '')
        
        # Remove encoding information from the end of lyrics
        song['lyrics'] = re.sub(encoding_re, '', song['lyrics'])
    
    # Write the modified list of song objects back to a new JSON file
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(songs, file, ensure_ascii=False, indent=4)

# Call the function with the path to JSON file
cleanse_lyrics(input_file_path, output_file_path, unwanted_string, encoding_pattern)

print("Lyrics cleansing complete. The cleaned data is saved to:", output_file_path)


#phrases:
# 1. 151you might also like
# 2. live for as low
