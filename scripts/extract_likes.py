"""Extract liked tweets from HAR file."""
import json
import sys
from pathlib import Path

def extract_likes(har_path, output_path):
    print(f"Loading HAR file: {har_path}")
    with open(har_path, "r", encoding="utf-8") as f:
        har = json.load(f)

    tweets = []
    seen_ids = set()

    for entry in har["log"]["entries"]:
        url = entry["request"]["url"]
        if "Likes" not in url and "likes" not in url:
            continue

        # Get response body
        try:
            body = entry["response"]["content"].get("text", "")
            if not body:
                continue
            data = json.loads(body)
        except (json.JSONDecodeError, KeyError):
            continue

        # Try multiple possible paths in the response
        instructions = None
        try:
            instructions = data["data"]["user"]["result"]["timeline_v2"]["timeline"]["instructions"]
        except (KeyError, TypeError):
            pass
        if not instructions:
            try:
                instructions = data["data"]["user"]["result"]["timeline"]["timeline"]["instructions"]
            except (KeyError, TypeError):
                pass
        if not instructions:
            try:
                instructions = data["data"]["user_result"]["result"]["timeline_v2"]["timeline"]["instructions"]
            except (KeyError, TypeError):
                pass
        if not instructions:
            continue

        for inst in instructions:
            entries_list = inst.get("entries", [])
            for e in entries_list:
                try:
                    item = e.get("content", {}).get("itemContent", {})
                    tr = item.get("tweet_results", {}).get("result", {})
                    if not tr:
                        continue

                    # Handle tweets wrapped in "tweet" key
                    if "tweet" in tr:
                        tr = tr["tweet"]

                    legacy = tr.get("legacy", {})
                    tweet_id = legacy.get("id_str") or tr.get("rest_id") or ""
                    if not tweet_id or tweet_id in seen_ids:
                        continue
                    seen_ids.add(tweet_id)

                    core = tr.get("core", {})
                    user_r = core.get("user_results", {}).get("result", {})
                    user_legacy = user_r.get("legacy", {})

                    screen_name = user_legacy.get("screen_name", "")

                    tweets.append({
                        "id": tweet_id,
                        "url": f"https://x.com/{screen_name}/status/{tweet_id}",
                        "text": legacy.get("full_text", ""),
                        "user": screen_name,
                        "user_name": user_legacy.get("name", ""),
                        "created_at": legacy.get("created_at", ""),
                        "retweet_count": legacy.get("retweet_count", 0),
                        "favorite_count": legacy.get("favorite_count", 0),
                    })
                except Exception:
                    continue

    print(f"Extracted {len(tweets)} unique tweets")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tweets, f, ensure_ascii=False, indent=2)
    print(f"Saved to: {output_path}")

if __name__ == "__main__":
    har_file = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\kaneko yu\Documents\jarvis-work\x_likes.har"
    out_file = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline\references\x_likes.json"

    # Make output directory
    Path(out_file).parent.mkdir(parents=True, exist_ok=True)

    extract_likes(har_file, out_file)