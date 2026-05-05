import hashlib
import os

class BloomFilter:
    def __init__(self, size: int = 1000000, hash_count: int = 3):
        self.size = size
        self.hash_count = hash_count
        self.bit_array = bytearray(size // 8 + 1)
    
    def _hashes(self, item: str) -> list[int]:
        result = []
        for i in range(self.hash_count):
            h = hashlib.md5(f"{item}{i}".encode()).hexdigest()
            result.append(int(h, 16) % self.size)
        return result
    
    def add(self, item: str) -> None:
        for h in self._hashes(item):
            byte_index = h // 8
            bit_index = h % 8
            self.bit_array[byte_index] |= (1 << bit_index)
    
    def contains(self, item: str) -> bool:
        for h in self._hashes(item):
            byte_index = h // 8
            bit_index = h % 8
            if not (self.bit_array[byte_index] & (1 << bit_index)):
                return False
        return True
    
    def save(self, filepath: str) -> None:
        with open(filepath, "wb") as f:
            f.write(self.bit_array)
    
    @classmethod
    def load(cls, filepath: str, size: int = 1000000, hash_count: int = 3) -> 'BloomFilter':
        bf = cls(size, hash_count)
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                bf.bit_array = bytearray(f.read())
        return bf

class MD5Deduplicator:
    def __init__(self):
        self.seen = set()
    
    def add(self, item: str) -> bool:
        md5_hash = hashlib.md5(item.encode()).hexdigest()
        if md5_hash in self.seen:
            return False
        self.seen.add(md5_hash)
        return True
    
    def contains(self, item: str) -> bool:
        md5_hash = hashlib.md5(item.encode()).hexdigest()
        return md5_hash in self.seen
    
    def save(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            for item in self.seen:
                f.write(item + "\n")
    
    @classmethod
    def load(cls, filepath: str) -> 'MD5Deduplicator':
        md5d = cls()
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    md5d.seen.add(line.strip())
        return md5d