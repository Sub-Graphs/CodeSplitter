from tree_sitter import Language, Parser
import tree_sitter_python

def print_methods_with_content(code):
    # Set up the parser
    PY_LANGUAGE = Language(tree_sitter_python.language())
    parser = Parser()
    parser.language = PY_LANGUAGE 

    # Parse the code
    tree = parser.parse(bytes(code, "utf8"))

    # Create a query to find function and method definitions
    query = PY_LANGUAGE.query(
        """
        (function_definition
          name: (identifier) @function.name
          body: (block) @function.body)
        (class_definition
          name: (identifier) @class.name
          body: (block (function_definition
            name: (identifier) @method.name
            body: (block) @method.body)))
        """
    )

    # Find all matches
    matches = query.captures(tree.root_node)

    # Print the function and method names and content
    print("Functions and methods defined in the program:")
    
    class_name = None
    for capture in matches:
        node, capture_name = capture
        
        if capture_name == "class.name":
            class_name = node.text.decode('utf8')
        elif capture_name in ["function.name", "method.name"]:
            name = node.text.decode('utf8')
            body_node = node.parent.child_by_field_name('body')
            
            if body_node:
                start_line, start_col = body_node.start_point
                end_line, end_col = body_node.end_point
                
                if class_name and capture_name == "method.name":
                    print(f"\n--- Method: {class_name}.{name} ---")
                else:
                    print(f"\n--- Function: {name} ---")
                
                # Extract and print the function content
                lines = code.split('\n')
                for i in range(start_line, end_line + 1):
                    if i == start_line:
                        print(lines[i][start_col:])
                    elif i == end_line:
                        print(lines[i][:end_col])
                    else:
                        print(lines[i])
                
                print("-------------------")
            
            if capture_name == "function.name":
                class_name = None  # Reset class_name for standalone functions

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

def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

class DataProcessor:
    def __init__(self, data):
        self.data = data

    def process(self):
        return [x * 2 for x in self.data]

    def filter_even(self):
        return [x for x in self.data if x % 2 == 0]

def main():
    # Generate a random list
    random_list = generate_random_list(10, 1, 100)
    print("Original list:", random_list)

    # Sort the list
    sorted_list = bubble_sort(random_list)
    print("Sorted list:", sorted_list)

    # Search for a value
    target = random.choice(sorted_list)
    index = binary_search(sorted_list, target)
    print(f"Found {target} at index {index}")

    # Process data
    processor = DataProcessor(sorted_list)
    processed_data = processor.process()
    print("Processed data:", processed_data)
    filtered_data = processor.filter_even()
    print("Filtered even numbers:", filtered_data)

if __name__ == "__main__":
    main()
"""

print_methods_with_content(code)