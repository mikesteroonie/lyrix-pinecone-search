import os
import json
import cohere
import pandas as pd
from dotenv import load_dotenv
from pinecone import Pinecone
import hashlib

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
def hash_text(text):
    """Generate a hash for a given text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def load_and_store_embeddings(artist):
    # df = pd.DataFrame()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    vector_id = 0  # Initialize vector ID for unique identification

    file_path = os.path.join(dir_path, f'{artist}_all_clean.json')
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
            pair_hash = hash_text(pair)
            if pair_hash not in unique_pairs and pair.strip():
                unique_pairs.add(pair_hash)
                
                stored_lyrics = pair.replace('\n', ', ')
                embed = co.embed(texts=[pair], input_type='search_document', model="embed-english-v3.0").embeddings[0]
            
                embeddings.append((str(vector_id), embed, {
                    'artist': artist,
                    'title': song['lyrics_title'],
                    'album': song['album'],
                    'lyrics': stored_lyrics
                }))
                vector_id += 1
    # Batch upsert
    batch_size = 100  # Adjust based on your needs
    async_results = []
    for chunk in chunks(embeddings, batch_size):
        ids_vectors_chunk = [(item[0], item[1]) for item in chunk]
        metadata_chunk = {item[0]: item[2] for item in chunk}
        async_result = index.upsert(vectors=ids_vectors_chunk, metadata=metadata_chunk, async_req=True)
        async_results.append(async_result)

    # Wait for and retrieve responses
    [async_result.get() for async_result in async_results]
    

    # # Drop duplicates based on title and album, as lyrics have been transformed
    # # df.drop_duplicates(subset=['lyrics_title', 'album'], inplace=True)
    # # Ensure no empty lines are processed
    # df = df[df['lyrics'].str.strip().astype(bool)]

    # for i, row in df.iterrows():
    #     for pair in row['paired_lyrics']:
    #         if pair.strip():  # Ensure the string is not empty
    #             # Create embedding for each pair of lyrics
    #             stored_lyrics = pair.replace('\n', ', ')
    #             embed = co.embed(texts=[pair], input_type='search_document', model="embed-english-v3.0").embeddings[0]

    #             # Store each pair as a separate vector in Pinecone
    #             index.upsert(vectors=[(str(vector_id), embed, {
    #                 'artist': artist,
    #                 'title': row['lyrics_title'], 
    #                 'album': row['album'], 
    #                 'lyrics': stored_lyrics  # Store the pair of lines as lyrics metadata
    #             })])
    #             vector_id += 1  # Increment vector ID for the next entry


def pair_lyrics(lyrics):
    """Pairs every two lines of lyrics."""
    lines = lyrics.split('\n')
    paired_lines = ['\n'.join(lines[i:i+2]) for i in range(0, len(lines) - 1, 2)]
    return paired_lines

if __name__ == "__main__":
    artists = ["drake", "kanye", "travis", "sza", "taylor"]
    # albums = ["all", "care_package", "dldt", "scorpion", "sfg", "sh12", "tml"]
    # albums = ["all", "care_package", "clb", "dldt", "fatd", "herLoss", "ml", "nwts", "scorpion", "sfg", "sh12", "takeCare", "tml", "views"]
    for artist in artists:
        print(f"Processing {artist}...")
        load_and_store_embeddings(artist)
    print("All embeddings have been stored.")

