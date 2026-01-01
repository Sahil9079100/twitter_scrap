import json
import glob
import os
from datetime import datetime
from collections import defaultdict

def parse_twitter_date(date_str):
    """Parses Twitter's date format into a datetime object."""
    if not date_str:
        return datetime.min
    try:
        # Format: "Tue Dec 30 19:40:53 +0000 2025"
        return datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
    except ValueError:
        return datetime.min

def mega_parse(username="output"):
    print(f"--- Starting Mega Parsing Process for {username} ---")
    
    all_tweets = {}
    
    # 1. Load all Timeline Batches (*_api_parsed.json)
    batch_files = glob.glob("*_api_parsed.json")
    print(f"Found {len(batch_files)} timeline batch files.")
    
    for fpath in batch_files:
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                tweets = json.load(f)
                for tweet in tweets:
                    tid = tweet.get('id')
                    if tid:
                        all_tweets[tid] = tweet
        except Exception as e:
            print(f"Error reading {fpath}: {e}")

    print(f"Total unique tweets after loading batches: {len(all_tweets)}")

    # 2. Load all Full Thread Files (thread_*_full.json)
    thread_files = glob.glob("thread_*_full.json")
    print(f"Found {len(thread_files)} full thread files.")
    
    for fpath in thread_files:
        try:
            # Extract thread_id from filename: thread_12345_full.json
            filename = os.path.basename(fpath)
            file_thread_id = filename.split('_')[1]
            
            with open(fpath, 'r', encoding='utf-8') as f:
                tweets = json.load(f)
                for tweet in tweets:
                    tid = tweet.get('id')
                    if tid:
                        # Ensure thread_id is set (it might be missing in some scrapes)
                        if not tweet.get('thread_id'):
                            tweet['thread_id'] = file_thread_id
                            tweet['is_thread'] = True
                            
                        # Overwrite/Update with data from thread file (usually more complete context)
                        all_tweets[tid] = tweet
        except Exception as e:
            print(f"Error reading {fpath}: {e}")

    print(f"Total unique tweets after loading threads: {len(all_tweets)}")

    # 3. Group by Thread ID
    standalone_tweets = []
    thread_groups = defaultdict(list)
    
    for tweet in all_tweets.values():
        thread_id = tweet.get('thread_id')
        
        # If it has a thread_id, add to group. 
        # Note: Some tweets might have thread_id == id (Root), they still go here first.
        if thread_id:
            thread_groups[thread_id].append(tweet)
        else:
            standalone_tweets.append(tweet)

    # 4. Process Thread Groups
    # We want to find the Root tweet for each group and nest the others under it.
    
    for tid, group in thread_groups.items():
        # Sort group by date
        group.sort(key=lambda x: parse_twitter_date(x.get('created_at')))
        
        # Find root (where id == thread_id)
        root_tweet = next((t for t in group if t.get('id') == tid), None)
        
        if root_tweet:
            # Separate replies
            replies = [t for t in group if t.get('id') != tid]
            
            # Nest replies inside root
            root_tweet['thread'] = replies
            
            # Add root to the main list
            standalone_tweets.append(root_tweet)
        else:
            # If no root found (e.g. we only scraped replies but not the parent),
            # treat them as individual tweets.
            # Alternatively, we could group them under a dummy container, 
            # but listing them individually is safer for now.
            standalone_tweets.extend(group)

    # 5. Final Sort by Date (Newest First)
    standalone_tweets.sort(key=lambda x: parse_twitter_date(x.get('created_at')), reverse=True)
    
    # 6. Save Output
    output_filename = f"{username}_mega_scrape.json"
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(standalone_tweets, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved {len(standalone_tweets)} items to {output_filename}")
    except Exception as e:
        print(f"Error saving output: {e}")

if __name__ == "__main__":
    mega_parse("adayendtrader")
