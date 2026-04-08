#!/usr/bin/env python3
import json
import re
import pyttsx3



# Print with (AREPL) prefix for better visibility in AREPL output
# ============================================
# WORD VALUE CALCULATOR
# ============================================

LETTER_VALUES = {
    'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,
    'j':1,'k':2,'l':3,'m':4,'n':5,'o':6,'p':7,'q':8,'r':9,
    's':1,'t':2,'u':3,'v':4,'w':5,'x':6,'y':7,'z':8,
    'ä':9,'ö':9,'ü':9
}

def compute_word_value(word):
    total = sum(LETTER_VALUES.get(ch.lower(), 0) for ch in word)
    reduced = sum(int(d) for d in str(total))
    while reduced > 9:
        reduced = sum(int(d) for d in str(reduced))
    return reduced


# ============================================
# PREFIX / SUFFIX DETECTION
# ============================================

COMMON_PREFIXES = [
    "anti","auto","bi","co","de","dis","en","ex","extra","hyper","inter",
    "intra","micro","mid","mis","mono","non","over","post","pre","pro",
    "re","semi","sub","super","trans","tri","un","under"
]

COMMON_SUFFIXES = [
    "able","age","al","ance","ant","ary","ate","ed","en","ence","ent",
    "er","est","ful","hood","ible","ic","ify","ing","ion","ish","ism",
    "ist","ity","ive","ize","less","ly","ment","ness","ology","ous","s","y"
]

def detect_prefixes(word):
    return [p for p in COMMON_PREFIXES if word.lower().startswith(p)]

def detect_suffixes(word):
    return [s for s in COMMON_SUFFIXES if word.lower().endswith(s)]


# ============================================
# AUDIO PRONUNCIATION ENGINE
# ============================================

tts_engine = pyttsx3.init()

def play_pronunciation(phonetic_text):
    if phonetic_text:
        tts_engine.say(phonetic_text)
        tts_engine.runAndWait()


# ============================================
# DICTIONARY LOOKUP PLACEHOLDERS
# (real versions added later)
# ============================================

def get_definition(word):
    return f"Definition for {word} (placeholder)"

def get_pronunciation(word):
    return f"/{word}/"

def get_synonyms(word):
    return ["synonym1", "synonym2"]


# ============================================
# ENTRY BUILDER
# ============================================

def build_entry(word):
    return {
        "word": word,
        "pronunciation": get_pronunciation(word),
        "definition": get_definition(word),
        "synonyms": get_synonyms(word),
        "prefixes": detect_prefixes(word),
        "suffixes": detect_suffixes(word),
        "value": compute_word_value(word)
    }


# ============================================
# OUTPUT FORMAT SELECTOR
# ============================================

def choose_output_format():
    print("\nSelect Output Format")
    print("A) JSON")
    print("B) TXT (dictionary-style)")
    print("C) Markdown (book-style)")
    print("D) All of the above")
    print("----------------------------------------")

    choice = input("Choose A, B, C, or D: ").strip().lower()

    if choice == "a":
        return ["json"]
    elif choice == "b":
        return ["txt"]
    elif choice == "c":
        return ["md"]
    elif choice == "d":
        return ["json", "txt", "md"]
    else:
        print("Invalid choice. Defaulting to JSON.")
        return ["json"]


# ============================================
# OUTPUT WRITERS
# ============================================

def write_json(entries):
    with open("dictionary_output.json", "w") as f:
        json.dump(entries, f, indent=4)

def write_txt(entries):
    with open("dictionary_output.txt", "w") as f:
        for e in entries:
            f.write(f"{e['word']}\n")
            f.write(f"  Pronunciation: {e['pronunciation']}\n")
            f.write(f"  Definition: {e['definition']}\n")
            f.write(f"  Synonyms: {', '.join(e['synonyms'])}\n")
            f.write(f"  Prefixes: {', '.join(e['prefixes'])}\n")
            f.write(f"  Suffixes: {', '.join(e['suffixes'])}\n")
            f.write(f"  Value: {e['value']}\n\n")

def write_markdown(entries):
    with open("dictionary_output.md", "w") as f:
        f.write("# Generated Dictionary\n\n")
        for e in entries:
            f.write(f"## {e['word']}\n")
            f.write(f"**Pronunciation:** {e['pronunciation']}\n\n")
            f.write(f"**Definition:** {e['definition']}\n\n")
            f.write(f"**Synonyms:** {', '.join(e['synonyms'])}\n\n")
            f.write(f"**Prefixes:** {', '.join(e['prefixes'])}\n\n")
            f.write(f"**Suffixes:** {', '.join(e['suffixes'])}\n\n")
            f.write(f"**Word Value:** {e['value']}\n\n")


# ============================================
# MAIN PROGRAM
# ============================================

def main():
    print("Dictionary Generator — Runtime Mode")
    print("A) WordNet + CMU (offline)")
    print("B) FreeDictionaryAPI (online)")
    print("C) Local word list file")
    print("----------------------------------------")

    mode = input("Choose A, B, or C: ").strip().lower()

    if mode == "c":
        path = input("Enter path to word list file: ").strip()
        try:
            with open(path, "r") as f:
                words = [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            print(f"Error: File '{path}' not found.")
            return
    else:
        words = ["example", "internet", "test"]

    output_formats = choose_output_format()

    entries = [build_entry(w) for w in words]

    if "json" in output_formats:
        write_json(entries)
    if "txt" in output_formats:
        write_txt(entries)
    if "md" in output_formats:
        write_markdown(entries)

    print("\nDictionary generated successfully.")


if __name__ == "__main__":
    main()