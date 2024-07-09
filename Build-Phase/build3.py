import re
from dataclasses import dataclass
from typing import List
from tree_sitter import Parser, Language, Tree, Node

@dataclass
class Span:
    start: int
    end: int

    def __add__(self, other):
        return Span(min(self.start, other.start), max(self.end, other.end))

    def __len__(self):
        return self.end - self.start

    def extract(self, source_code: bytes):
        return source_code[self.start:self.end]

def non_whitespace_len(text: bytes) -> int:
    return len(re.sub(rb'\s', b'', text))

def get_line_number(byte_offset: int, source_code: bytes) -> int:
    return source_code[:byte_offset].count(b'\n') + 1

def chunker(
    tree: Tree,
    source_code: bytes,
    MAX_CHARS=512 * 3,
    coalesce=50  # Any chunk less than 50 characters long gets coalesced with the next chunk
) -> List[Span]:

    # 1. Recursively form chunks
    def chunk_node(node: Node) -> List[Span]:
        chunks: List[Span] = []
        current_chunk: Span = Span(node.start_byte, node.start_byte)
        node_children = node.children
        for child in node_children:
            if child.end_byte - child.start_byte > MAX_CHARS:
                chunks.append(current_chunk)
                current_chunk = Span(child.end_byte, child.end_byte)
                chunks.extend(chunk_node(child))
            elif child.end_byte - child.start_byte + len(current_chunk) > MAX_CHARS:
                chunks.append(current_chunk)
                current_chunk = Span(child.start_byte, child.end_byte)
            else:
                current_chunk += Span(child.start_byte, child.end_byte)
        chunks.append(current_chunk)
        return chunks
    
    chunks = chunk_node(tree.root_node)

    # 2. Filling in the gaps
    for prev, curr in zip(chunks[:-1], chunks[1:]):
        prev.end = curr.start
    chunks[-1].end = tree.root_node.end_byte

    # 3. Combining small chunks with bigger ones
    new_chunks = []
    current_chunk = Span(0, 0)
    for chunk in chunks:
        current_chunk += chunk
        if non_whitespace_len(current_chunk.extract(source_code)) > coalesce \
            and b"\n" in current_chunk.extract(source_code):
            new_chunks.append(current_chunk)
            current_chunk = Span(chunk.end, chunk.end)
    if len(current_chunk) > 0:
        new_chunks.append(current_chunk)

    # 4. Changing line numbers
    line_chunks = [Span(get_line_number(chunk.start, source_code),
                        get_line_number(chunk.end, source_code)) for chunk in new_chunks]

    # 5. Eliminating empty chunks
    line_chunks = [chunk for chunk in line_chunks if len(chunk) > 0]

    return line_chunks

def setup_parser(language: str) -> Parser:
    # You need to build the language library beforehand and provide the correct path
    LANGUAGE_SO_PATH = f'./build/my-languages.so'
    language_library = Language(LANGUAGE_SO_PATH, language)
    parser = Parser()
    parser.set_language(language_library)
    return parser

def main():
    # Example usage
    python_code = b"""
def hello_world():
    print("Hello, World!")

class ExampleClass:
    def __init__(self):
        self.value = 42

    def get_value(self):
        return self.value

if __name__ == "__main__":
    hello_world()
    obj = ExampleClass()
    print(obj.get_value())
"""

    parser = setup_parser('python')
    tree = parser.parse(python_code)
    chunks = chunker(tree, python_code)

    print("Chunked code (line numbers):")
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}: Lines {chunk.start}-{chunk.end}")
        print(python_code[chunk.start:chunk.end].decode('utf-8'))
        print("-" * 40)

if __name__ == "__main__":
    main()