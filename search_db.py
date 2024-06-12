import os
import cohere
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

# Cohere API key
cohere_api_key = os.getenv('COHERE_API_KEY')
co = cohere.Client(cohere_api_key)

# Pinecone setup
pinecone_api_key = os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key=pinecone_api_key)  # Updated initialization

index_name = 'lyrix'
index = pc.Index(index_name)  # Use the Pinecone instance to access the Index

# def search_lyrics(query):
#     # Create the query embedding, specifying it's a search query
#     query_embedding = co.embed(texts=[query], model="embed-english-v3.0", input_type='search_query').embeddings[0]
#     results = index.query(vector=query_embedding, top_k=10, include_metadata=True)

#     for match in results['matches']:
#         print(f"Score: {match['score']:.2f}, Title: {match['metadata']['title']}, Album: {match['metadata']['album']}, Lyrics: {match['metadata']['lyrics']}")

# NOTE: limits to 2 vectors per song--would work if sanitized still returning 10

def search_lyrics(query, artist):
    # Create the query embedding, specifying it's a search query
    query_embedding = co.embed(texts=[query], model="embed-english-v3.0", input_type='search_query').embeddings[0]
    results = index.query(vector=query_embedding, top_k=100, include_metadata=True)

    # Initialize a dictionary to track the number of times vectors from each song are added
    song_count = {}
    
    # Initialize a list to store matches for filtered results
    filtered_results = []

    for match in results['matches']:
        # check to see if right artist
        if artist and match['metadata'].get('artist') != artist:
            continue
        # Use title and album as a composite key to uniquely identify a song
        song_key = (match['metadata']['title'], match['metadata']['album'])
        
        # Check if the song has already been added twice
        if song_count.get(song_key, 0) < 2:
            # Update the song count
            song_count[song_key] = song_count.get(song_key, 0) + 1
            
            # Add this match to filtered results
            filtered_results.append(match)

    # Print the first 10 or fewer filtered results
    for i, match in enumerate(filtered_results[:10], start=1):
        # Format the lyrics for readability
        formatted_lyrics = match['metadata']['lyrics'].replace('\n', ' / ')
        
        print(f"{i}. Score: {match['score']:.2f}, Title: {match['metadata']['title']}, Album: {match['metadata']['album']}, Lyrics: {formatted_lyrics}")

if __name__ == "__main__":
    query = "are you dumb"
    artist = "kanye"
    search_lyrics(query, artist)




# NOTE: doesn't limit to two vectors per song

# def search_lyrics(query):
#     # Create the query embedding, specifying it's a search query
#     query_embedding = co.embed(texts=[query], model="embed-english-v3.0", input_type='search_query').embeddings[0]
#     results = index.query(vector=query_embedding, top_k=10, include_metadata=True)

#     for i, match in enumerate(results['matches'], start=1):
#         # Format the lyrics for readability
#         formatted_lyrics = match['metadata']['lyrics'].replace('\n', ' / ')
#         # print(f"Score: {match['score']:.2f}, Title: {match['metadata']['title']}, Album: {match['metadata']['album']}, Lyrics: {formatted_lyrics}")
#         print(f"{i}. Score: {match['score']:.2f}, Lyrics: {formatted_lyrics}")



# if __name__ == "__main__":
#     query = "I think I have feelings for you"
#     search_lyrics(query)
