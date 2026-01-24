# KeywordExtractor Contract

> Authority: CONTRACT (Level 2, Binding)

## Purpose
Define the deterministic behavior of `KeywordExtractor.extract` so keyword ordering is stable across runs.

## Inputs
- **text**: Source text to analyze.
- **top_n**: Maximum number of keywords to return.

## Tokenization & Filtering
- Tokens are extracted using the regex `\b[a-zA-Z]{3,}\b` and lowercased.
- Stopwords are removed using `KeywordExtractor.STOPWORDS`.

## Scoring
- Each keyword receives a score equal to its frequency count in the filtered token list.

## Sorting (Deterministic Tie-Break)
Keywords are sorted using the following keys in order:
1. **Primary**: score descending (higher frequency first)
2. **Secondary**: first occurrence position ascending (earlier in the filtered token list first)
3. **Tertiary**: keyword lexicographic order ascending (dictionary order)

## Output
- Returns a list of `(keyword, count)` tuples ordered by the deterministic sort described above.
- The list is truncated to `top_n` entries.
