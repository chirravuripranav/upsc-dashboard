import sys
import os
import time
from youtube_transcript_api import YouTubeTranscriptApi
from groq import Groq
import dotenv

# Load environment
dotenv.load_dotenv('.env')
groq_api_key = os.environ.get('GROQ_API_KEY')
if not groq_api_key:
    # check parent directory as fallback
    parent_env = r'..\.env'
    if os.path.exists(parent_env):
        dotenv.load_dotenv(parent_env)
        groq_api_key = os.environ.get('GROQ_API_KEY')

if not groq_api_key:
    print("ERROR: GROQ_API_KEY not found.")
    sys.exit(1)

client = Groq(api_key=groq_api_key)

def chunk_transcript(transcript, chunk_size=3000):
    chunks = []
    current_chunk = ""
    word_count = 0
    for entry in transcript:
        text = entry['text']
        words = text.split()
        if word_count + len(words) > chunk_size:
            chunks.append(current_chunk)
            current_chunk = text + " "
            word_count = len(words)
        else:
            current_chunk += text + " "
            word_count += len(words)
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def generate_notes(video_id, subject_context, output_file):
    print(f"[*] Fetching transcript for {video_id}...")
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi'])
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return

    print(f"[*] Transcript fetched. Chunking...")
    chunks = chunk_transcript(transcript, chunk_size=2500)
    print(f"[*] Total Chunks: {len(chunks)}")
    
    final_notes = f"# Video Notes for {video_id}\n\n"
    
    for i, chunk in enumerate(chunks):
        print(f"[*] Processing Chunk {i+1}/{len(chunks)} with Groq AI...")
        prompt = f"""You are an elite UPSC Faculty making standard-book level notes (like Laxmikanth or Spectrum).
Context Subject: {subject_context}

Here is a raw transcript chunk from a lecture:
{chunk}

Please convert this transcript into highly structured, premium UPSC study notes.
- Use H2/H3 Markdown headings.
- Use bullet points for concepts, causes, consequences.
- Filter out conversational filler ("hello students", "like and subscribe").
- Elevate the language to a standard textbook level suitable for a beginner to advanced UPSC aspirant.
- If the transcript stops mid-sentence (as it's a chunk), just gracefully wrap up the final point.
"""
        try:
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2500
            )
            notes = completion.choices[0].message.content
            final_notes += notes + "\n\n---\n\n"
            print(f"[+] Chunk {i+1} completed.")
        except Exception as e:
            print(f"[-] Error processing chunk {i+1}: {e}")
        
        # Avoid rate limits
        time.sleep(2)
        
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_notes)
    
    print(f"[SUCCESS] Notes saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python generate_notes.py <youtube_video_id> <subject_context> <output_file.md>")
        sys.exit(1)
        
    v_id = sys.argv[1]
    ctx = sys.argv[2]
    out = sys.argv[3]
    generate_notes(v_id, ctx, out)
