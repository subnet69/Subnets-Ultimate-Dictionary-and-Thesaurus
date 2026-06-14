#!/usr/bin/env python3
import json
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import importlib
from pathlib import Path

#Print with (AREPL) prefix for better visibility in AREPL output
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
# ==========================================
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
    word_lower = word.lower()
    matches = []
    for p in COMMON_PREFIXES:
        if word_lower.startswith(p):
            root = word_lower[len(p):]
            if len(root) >= 3:  # Root must be at least 3 chars
                matches.append(p)
    return matches

def detect_suffixes(word):
    word_lower = word.lower()
    matches = []
    for s in COMMON_SUFFIXES:
        if word_lower.endswith(s):
            root = word_lower[:-len(s)]
            if len(root) >= 3:  # Root must be at least 3 chars
                matches.append(s)
    return matches


# ============================================
# AUDIO PRONUNCIATION ENGINE
# ============================================

def is_gtts_available():
    try:
        from gtts import gTTS  # noqa: F401
        return True
    except ImportError:
        return False


def is_local_tts_available():
    try:
        import pyttsx3  # noqa: F401
        return True
    except ImportError:
        return bool(shutil.which("espeak") or shutil.which("spd-say"))


def play_audio_file(path):
    try:
        from playsound import playsound
        playsound(path)
        return
    except Exception:
        pass

    for player in ("mpg123", "mpg321", "mpv", "cvlc", "ffplay", "xdg-open"):
        if shutil.which(player):
            try:
                args = [player, path]
                if player == "ffplay":
                    args = [player, "-nodisp", "-autoexit", path]
                subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except Exception:
                continue

    print(f"Audio file saved: {path}")
    print("Install `playsound`, `mpg123`, `mpv`, or `xdg-open` to play it automatically.")


def choose_voice_engine():
    print("\nSelect Voice Engine")
    print("A) Google TTS (requires internet)")
    print("B) Local TTS (espeak/pyttsx3 on Linux)")
    print("C) None")
    print("----------------------------------------")

    choice = input("Choose A, B, or C: ").strip().lower()
    if choice == "a":
        if not is_gtts_available():
            print("Google TTS is not available. Install `gtts` to use this option.")
            return None
        return "google"
    if choice == "b":
        if not is_local_tts_available():
            print("Local TTS is not available. Install `pyttsx3`, `espeak`, or `spd-say`.")
            return None
        return "local"
    return None


def speak_with_google(text):
    try:
        from gtts import gTTS
    except ImportError:
        print("Google TTS is not installed. Install `gtts` to enable speech.")
        return

    output_path = Path("pronunciation_google.mp3")
    tts = gTTS(text=text, lang="en")
    tts.save(str(output_path))
    print(f"Saved Google TTS audio to {output_path}")
    play_audio_file(str(output_path))


def speak_with_local_engine(text):
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        return
    except Exception:
        pass

    if shutil.which("espeak"):
        subprocess.run(["espeak", text], check=False)
        return

    if shutil.which("spd-say"):
        subprocess.run(["spd-say", text], check=False)
        return

    print("Local TTS is not available on this system.")


def fetch_free_dictionary_data(word):
    url = "https://api.dictionaryapi.dev/api/v2/entries/en/" + urllib.parse.quote(word)
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                print(f"FreeDictionaryAPI returned status {response.status} for {word}")
                return {}
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 403:
            print(f"FreeDictionaryAPI blocked request for {word} (403). Try a simpler word or check internet connection.")
        elif exc.code == 404:
            print(f"Word not found: {word}")
        else:
            print(f"FreeDictionaryAPI HTTP error for {word}: {exc.code} {exc.reason}")
        return {}
    except urllib.error.URLError as exc:
        print(f"FreeDictionaryAPI network error for {word}: {exc.reason}")
        return {}
    except Exception as exc:
        print(f"Unexpected error fetching {word}: {exc}")
        return {}

    if not isinstance(data, list) or not data:
        return {}

    first = data[0]
    pronunciation = None
    for phonetic in first.get("phonetics", []):
        if phonetic.get("text"):
            pronunciation = phonetic["text"]
            break
    if not pronunciation:
        pronunciation = first.get("word", word)

    definitions = []
    synonyms = []
    for meaning in first.get("meanings", []):
        for definition in meaning.get("definitions", []):
            if definition.get("definition"):
                definitions.append(definition["definition"])
        synonyms.extend(meaning.get("synonyms", []))


    return {
        "pronunciation": pronunciation,
        "definition": definitions[0] if definitions else f"Definition for {word} (not available)",
        "synonyms": list(dict.fromkeys(synonyms))[:8]
    }


# ============================================
# DICTIONARY LOOKUP PLACEHOLDERS
# (real versions added later)
# ============================================

def get_definition(word, lookup_data=None):
    if lookup_data and lookup_data.get("definition"):
        return lookup_data["definition"]
    return f"Definition for {word} (not available)"

def get_pronunciation(word, lookup_data=None):
    if lookup_data and lookup_data.get("pronunciation"):
        return lookup_data["pronunciation"]
    return f"/{word}/"

def get_synonyms(word, lookup_data=None):
    if lookup_data and lookup_data.get("synonyms"):
        return lookup_data["synonyms"]
    return []


# ============================================
# ENTRY BUILDER
# ============================================

def build_entry(word, lookup_data=None):
    return {
        "word": word,
        "pronunciation": get_pronunciation(word, lookup_data),
        "definition": get_definition(word, lookup_data),
        "synonyms": get_synonyms(word, lookup_data),
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
        return choose_output_format()     
    


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



def main():
    print("Dictionary Generator — Runtime Mode")
    print("A) WordNet + CMU (offline)")
    print("B) FreeDictionaryAPI (online)")
    print("C) Local word list file")
    print("----------------------------------------")

    mode = input("Choose A, B, or C: ").strip().lower()
    lookup_data = {}

    if mode == "c":
        path = input("Enter path to word list file: ").strip()
        with open(path, "r") as f:
            words = [line.strip() for line in f.readlines() if line.strip()]
    elif mode == "b":
        words = []
        print("Enter words to look up with FreeDictionaryAPI. Leave blank to finish.")
        while True:
            word = input("Word: ").strip()
            if not word:
                break
            words.append(word)
        if not words:
            words = ["No Match Found"]
        lookup_data = {word: fetch_free_dictionary_data(word) for word in words}
    else:
        print("Offline lookup is not implemented yet. Using fallback words.")
        words = ["example", "internet", "test"]

    output_formats = choose_output_format()
    voice_engine = choose_voice_engine()

    entries = [build_entry(w, lookup_data.get(w)) for w in words]

    if "json" in output_formats:
        write_json(entries)
    if "txt" in output_formats:
        write_txt(entries)
    if "md" in output_formats:
        write_markdown(entries)

    if voice_engine == "google":
        for entry in entries:
            speak_with_google(entry["word"])
    elif voice_engine == "local":
        for entry in entries:
            speak_with_local_engine(entry["word"])

    print("\nDictionary generated successfully.")


if __name__ == "__main__":
    main()
