import os
import json
import cohere
import pandas as pd
from dotenv import load_dotenv
from pinecone import Pinecone
import hashlib
import re

load_dotenv()
pd.set_option('display.max_colwidth', None)

# Cohere API key
cohere_api_key = os.getenv('COHERE_API_KEY')
co = cohere.Client(cohere_api_key)

# Pinecone setup
pinecone_api_key = os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key=pinecone_api_key, pool_threads = 30)  # Create an instance of the Pinecone class

index_name = 'lyrix'
index = pc.Index(index_name)  # Use the instance to access the Index
vector_id_global = 0  # Initialize outside the function
def hash_text(text):
    """Generate a hash for a given text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
def generate_vector_id(artist, title, lyrics):
    """
    Generate a hash-based ID for the vector using the artist, title, and lyrics.
    """
    hash_input = f"{artist}-{title}-{lyrics}"
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()


def load_and_store_embeddings(artist, test_mode, test_limit):
    # df = pd.DataFrame()
    global vector_id_global
    dir_path = os.path.dirname(os.path.realpath(__file__))
    # vector_id = 0  # Initialize vector ID for unique identification
    pairs_processed = 0

    file_path = os.path.join(dir_path, artist, f'{artist}_all_clean.json')
    with open(file_path) as f:
        data = json.load(f)
    unique_pairs = set()
    embeddings = []

    # album_df = pd.DataFrame(data)
    # df = pd.concat([df, album_df], ignore_index=True)
    # Adjust each song's data to pair every two lines of lyrics
    for song in data:
        # Create pairs of every two lines
        paired_lyrics = pair_lyrics(song['lyrics'])
        # Update song's lyrics with paired lines
        song['paired_lyrics'] = paired_lyrics
        for pair in paired_lyrics:
            if test_mode and pairs_processed >= test_limit:
                break
            pair_hash = hash_text(pair)
            if pair_hash not in unique_pairs and pair.strip():
                unique_pairs.add(pair_hash)
                
                stored_lyrics = pair.replace('\n', ', ')
                
                embed = co.embed(texts=[pair], input_type='search_document', model="embed-english-v3.0").embeddings[0]

                vector_id = generate_vector_id(artist, song['lyrics_title'], stored_lyrics)  # Using the new function to generate a hash-based ID
                embeddings.append((vector_id, embed, {
                    'artist': artist,
                    'title': song['lyrics_title'],
                    'album': song['album'],
                    'lyrics': stored_lyrics
                }))
                vector_id_global += 1
                pairs_processed+=1
        if test_mode and pairs_processed >= test_limit:
            break #breaking so we don't do whole discovgraphy during testing
    # Batch upsert
    batch_size = 100  
    async_results = []

    for chunk in chunks(embeddings, batch_size):
        to_upsert = [(item[0], item[1], item[2]) for item in chunk]

        print(to_upsert[3])
        # Upsert the batch of vectors with their metadata
        async_result = index.upsert(vectors=to_upsert, async_req=True)
        async_results.append(async_result)


    # Wait for and retrieve responses
    [async_result.get() for async_result in async_results]
    

def pair_lyrics(lyrics):
    """Pairs every two lines of lyrics."""
    lines = lyrics.split('\n')
    paired_lines = ['\n'.join(lines[i:i+2]) for i in range(0, len(lines) - 1, 2)]
    return paired_lines

if __name__ == "__main__":
    # artists = ["travis"]
    artists = ["drake", "future", "kanye", "sza", "taylor", "travis", "weeknd"]
    # albums = ["all", "care_package", "dldt", "scorpion", "sfg", "sh12", "tml"]
    # albums = ["all", "care_package", "clb", "dldt", "fatd", "herLoss", "ml", "nwts", "scorpion", "sfg", "sh12", "takeCare", "tml", "views"]
    for artist in artists:
        print(f"Processing {artist}...")
        load_and_store_embeddings(artist, False, 10)
    print("All embeddings have been stored.")

