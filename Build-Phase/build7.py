from tree_sitter import Language, Parser
import tree_sitter_python
import networkx as nx
import matplotlib.pyplot as plt

def setup_parser():
    PY_LANGUAGE = Language(tree_sitter_python.language())
    parser = Parser()
    parser.language = PY_LANGUAGE
    return parser

def identify_constructs(code, parser):
    tree = parser.parse(bytes(code, "utf8"))
    
    query = parser.language.query(
        """
        (module) @module
        (class_definition
          name: (identifier) @class.name) @class
        (function_definition
          name: (identifier) @function.name) @function
        (import_statement) @import
        (import_from_statement) @import_from
        (assignment
          left: (identifier) @global_var
          right: (_)) @global_assignment
        """
    )
    
    constructs = {
        'module': [],
        'class': [],
        'function': [],
        'method': [],
        'import': [],
        'global_var': []
    }
    
    matches = query.captures(tree.root_node)
    current_class = None
    
    for node, node_type in matches:
        if node_type == 'module':
            constructs['module'].append(('module', 'module'))
        elif node_type == 'class':
            class_name = node.child_by_field_name('name').text.decode('utf8')
            constructs['class'].append((class_name, 'class'))
            current_class = class_name
        elif node_type == 'function':
            func_name = node.child_by_field_name('name').text.decode('utf8')
            if current_class:
                constructs['method'].append((f"{current_class}.{func_name}", 'method'))
            else:
                constructs['function'].append((func_name, 'function'))
        elif node_type in ['import', 'import_from']:
            constructs['import'].append((node.text.decode('utf8').split()[1], 'import'))
        elif node_type == 'global_var':
            var_name = node.text.decode('utf8')
            constructs['global_var'].append((var_name, 'global_var'))
    
    return constructs

def create_relations(constructs):
    G = nx.DiGraph()
    
    for construct_type, items in constructs.items():
        for item, item_type in items:
            G.add_node(item, type=item_type)
    
    # Add hierarchical relations
    for class_name, _ in constructs['class']:
        G.add_edge('module', class_name)
    
    for func_name, _ in constructs['function']:
        G.add_edge('module', func_name)
    
    for method_name, _ in constructs['method']:
        class_name = method_name.split('.')[0]
        G.add_edge(class_name, method_name)
    
    for import_name, _ in constructs['import']:
        G.add_edge('module', import_name)
    
    for var_name, _ in constructs['global_var']:
        G.add_edge('module', var_name)
    
    return G

def visualize_graph(G):
    pos = nx.spring_layout(G, k=0.9, iterations=50)
    
    node_colors = ['lightblue' if G.nodes[node]['type'] == 'module' else
                   'lightgreen' if G.nodes[node]['type'] == 'class' else
                   'pink' if G.nodes[node]['type'] == 'method' else
                   'yellow' if G.nodes[node]['type'] == 'function' else
                   'orange' if G.nodes[node]['type'] == 'import' else
                   'lightgrey' for node in G.nodes()]
    
    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=3000, font_size=8, font_weight='bold')
    
    legend_elements = [plt.Rectangle((0,0),1,1,fc="lightblue", label="Module"),
                       plt.Rectangle((0,0),1,1,fc="lightgreen", label="Class"),
                       plt.Rectangle((0,0),1,1,fc="pink", label="Method"),
                       plt.Rectangle((0,0),1,1,fc="yellow", label="Function"),
                       plt.Rectangle((0,0),1,1,fc="orange", label="Import"),
                       plt.Rectangle((0,0),1,1,fc="lightgrey", label="Global Var")]
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.title("Code Structure Graph")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

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


parser = setup_parser()
constructs = identify_constructs(code, parser)
G = create_relations(constructs)
visualize_graph(G)