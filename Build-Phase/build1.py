import os
import subprocess
import logging
from tree_sitter import Language, Parser

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LANGUAGE_NAMES = ["python", "java", "cpp", "go", "rust", "ruby", "php"]
MAX_CHARS = 1500
CHUNK_SIZE = 50  # for naive chunking
OVERLAP = 10  # for naive chunking

def setup_languages():
    languages = {}
    for language in LANGUAGE_NAMES:
        # Clone the repository if it doesn't exist
        if not os.path.exists(f"cache/tree-sitter-{language}"):
            subprocess.run(f"git clone https://github.com/tree-sitter/tree-sitter-{language} cache/tree-sitter-{language}", shell=True)
        
        # Build the language library
        Language.build_library(
            f'cache/build/{language}.so',
            [f"cache/tree-sitter-{language}"]
        )
        
        # Create language object
        languages[language] = Language(f"cache/build/{language}.so", language)
    
    return languages

def chunk_node(node, text, max_chars=MAX_CHARS):
    new_chunks = []
    current_chunk = ""
    for child in node.children:
        child_text = text[child.start_byte:child.end_byte]
        if len(child_text) > max_chars:
            if current_chunk:
                new_chunks.append(current_chunk)
                current_chunk = ""
            new_chunks.extend(chunk_node(child, text, max_chars))
        elif len(current_chunk) + len(child_text) > max_chars:
            new_chunks.append(current_chunk)
            current_chunk = child_text
        else:
            current_chunk += child_text
    
    if current_chunk:
        new_chunks.append(current_chunk)
    
    return new_chunks

def chunk(text, languages, max_chars=MAX_CHARS):
    # Determining the language
    file_language = None
    for language_name, language in languages.items():
        parser = Parser()
        parser.set_language(language)
        tree = parser.parse(bytes(text, "utf-8"))
        if not tree.root_node.children or tree.root_node.children[0].type != "ERROR":
            file_language = language
            break
        logger.warning(f"Not language {language_name}")
    
    # Smart chunker
    if file_language:
        return chunk_node(tree.root_node, text, max_chars)
    
    # Naive algorithm
    logger.warning("Falling back to naive chunking")
    source_lines = text.split('\n')
    num_lines = len(source_lines)
    logger.info(f"Number of lines: {num_lines}")
    chunks = []
    start_line = 0
    while start_line < num_lines:
        end_line = min(start_line + CHUNK_SIZE, num_lines)
        chunk = '\n'.join(source_lines[start_line:end_line])
        chunks.append(chunk)
        start_line += CHUNK_SIZE - OVERLAP
    
    return chunks

def main():
    # Setup languages
    languages = setup_languages()
    
    # Example usage
    sample_code = """
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
    
    chunks = chunk(sample_code, languages)
    
    print("Chunked code:")
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}:")
        print(chunk)
        print("-" * 40)

if __name__ == "__main__":
    main()