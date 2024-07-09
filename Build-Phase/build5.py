from tree_sitter import Language, Parser
import tree_sitter_python

def print_ast_tree(code):
    # Set up the parser
    PY_LANGUAGE = Language(tree_sitter_python.language())
    parser = Parser()
    parser.language = PY_LANGUAGE
   
    # Parse the code
    tree = parser.parse(bytes(code, "utf8"))
   
    def traverse_tree(node, prefix="", is_last=True):
        # Print the current node
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{node.type}: {node.text.decode('utf-8')[:20]}")
       
        # Prepare the prefix for children
        child_prefix = prefix + ("    " if is_last else "│   ")
       
        # Traverse children
        children = node.children
        for i, child in enumerate(children):
            traverse_tree(child, child_prefix, i == len(children) - 1)

    traverse_tree(tree.root_node)

# Example code
code = """
import random

def generate_random_list(size, min_val, max_val):
    return [random.randint(min_val, max_val) for _ in range(size)]

def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

class DataProcessor:
    def __init__(self, data):
        self.data = data

    def process(self):
        return [x * 2 for x in self.data]

if __name__ == "__main__":
    main()
"""

print_ast_tree(code)