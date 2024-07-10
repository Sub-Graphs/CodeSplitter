from tree_sitter import Language, Parser
import tree_sitter_python
import networkx as nx
import matplotlib.pyplot as plt

def create_code_structure_graph(code):
    # Set up the parser
    PY_LANGUAGE = Language(tree_sitter_python.language())
    parser = Parser()
    parser.language = PY_LANGUAGE
    
    # Parse the code
    tree = parser.parse(bytes(code, "utf8"))
    
    # Create a NetworkX graph
    G = nx.DiGraph()
    
    # Create a query to find modules, classes, functions, and methods
    query = PY_LANGUAGE.query(
        """
        (module) @module
        (class_definition
          name: (identifier) @class.name) @class
        (function_definition
          name: (identifier) @function.name) @function
        """
    )
    
    # Find all matches
    matches = query.captures(tree.root_node)
    
    # Add nodes and edges to the graph
    current_class = None
    G.add_node('module', type='module')
    
    for node, node_type in matches:
        if node_type == 'class':
            class_name_node = node.child_by_field_name('name')
            if class_name_node:
                class_name = class_name_node.text.decode('utf8')
                G.add_node(class_name, type='class')
                G.add_edge('module', class_name)
                current_class = class_name
        elif node_type == 'function':
            func_name_node = node.child_by_field_name('name')
            if func_name_node:
                func_name = func_name_node.text.decode('utf8')
                if current_class:
                    full_name = f"{current_class}.{func_name}"
                    G.add_node(full_name, type='method')
                    G.add_edge(current_class, full_name)
                else:
                    G.add_node(func_name, type='function')
                    G.add_edge('module', func_name)
    
    return G

def visualize_graph(G):
    pos = nx.spring_layout(G, k=0.9, iterations=50)
    
    node_colors = ['lightblue' if G.nodes[node]['type'] == 'module' else
                   'lightgreen' if G.nodes[node]['type'] == 'class' else
                   'pink' if G.nodes[node]['type'] == 'method' else
                   'yellow' for node in G.nodes()]
    
    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=3000, font_size=8, font_weight='bold')
    
    # Add a legend
    legend_elements = [plt.Rectangle((0,0),1,1,fc="lightblue", label="Module"),
                       plt.Rectangle((0,0),1,1,fc="lightgreen", label="Class"),
                       plt.Rectangle((0,0),1,1,fc="pink", label="Method"),
                       plt.Rectangle((0,0),1,1,fc="yellow", label="Function")]
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.title("Code Structure Graph")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# Example code
code = """
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)

class MathOperations:
    def __init__(self):
        self.result = 0

    def calculate_factorial(self, n):
        self.result = factorial(n)
        return self.result

    def double(self, x):
        return x * 2

def main():
    math_ops = MathOperations()
    result = math_ops.calculate_factorial(5)
    print(result)
    print(math_ops.double(result))

if __name__ == "__main__":
    main()
"""

# Create code structure graph
G = create_code_structure_graph(code)

# Visualize the graph
visualize_graph(G)