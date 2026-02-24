import hashlib
import secrets
from Encryption.wordlist import WORDLIST


class SeedPhrase:
    
    @staticmethod
    def generate_phrase(word_count: int = 12) -> list:
        if word_count > len(WORDLIST):
            raise ValueError(f"Cannot pick {word_count} unique words from {len(WORDLIST)}-word list.")
        return secrets.SystemRandom().sample(WORDLIST, word_count)
    
    @staticmethod
    def phrase_to_password(seed_phrase: list) -> str:
        if isinstance(seed_phrase, str):
            seed_phrase = seed_phrase.split()
        
        phrase_str = " ".join(seed_phrase).lower()
        return phrase_str
    
    @staticmethod
    def validate_phrase(seed_phrase: list) -> tuple:
        if not isinstance(seed_phrase, list):
            return False, "Seed phrase must be a list"
        
        if len(seed_phrase) != 12:
            return False, f"Seed phrase must have 12 words, got {len(seed_phrase)}"
        
        for word in seed_phrase:
            if word not in WORDLIST:
                return False, f"Invalid word in seed phrase: {word}"
        
        return True, "Valid seed phrase"


class SeedPhraseAuth:
    def __init__(self):
        self.user_id = None
        self.stored_hash = None

    def _phrase_to_hash(self, phrase) -> str:
        if isinstance(phrase, list):
            phrase = " ".join(phrase)
        return hashlib.sha256(phrase.strip().encode("utf-8")).hexdigest()

    def generate_phrase(self, word_count: int = 12) -> list:
        if word_count > len(WORDLIST):
            raise ValueError(f"Cannot pick {word_count} unique words from {len(WORDLIST)}-word list.")
        return secrets.SystemRandom().sample(WORDLIST, word_count)

    def register(self, user_id: str, seed_phrase: list) -> tuple:
        self.user_id = user_id
        self.stored_hash = self._phrase_to_hash(seed_phrase)
        return True, f"User '{user_id}' registered"

    def verify(self, user_id: str, seed_phrase: list) -> tuple:
        if user_id != self.user_id:
            return False, f"User '{user_id}' not found"
        
        phrase_hash = self._phrase_to_hash(seed_phrase)
        if phrase_hash != self.stored_hash:
            return False, "Invalid seed phrase"
        
        return True, f"User '{user_id}' authenticated"
