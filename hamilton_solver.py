import constraints
import pycosat

class HamiltonSolver:

    def __init__(self):
        self.variable_map = {}
        self.counter = 1
        self.G = []
        self.clauses = []

    def read_file(self, filename):
        edges = []
        record_edges = False

        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith("DIMENSION"):
                    dimension = int(line.split(":")[1].strip())
                elif line.startswith("EDGE_DATA_SECTION"):
                    record_edges = True
                elif line.startswith("-1"):
                    break
                elif record_edges:
                    edge = list(map(int, line.split()))
                    edges.append(edge)

        self.G = [[] for _ in range(dimension)]

        for edge in edges:
            u, v = edge[0] - 1, edge[1] - 1
            self.G[u].append(v)
            self.G[v].append(u)

    
    def full_encoding(self):
        n = len(self.G)
        
        self.clauses = [
            *constraints.successor_constraint_1(self),
            *constraints.successor_constraint_2(self),
            *constraints.successor_constraint_3(self),
            *constraints.successor_constraint_4(self),
            *constraints.optimized_ordering_constraint_1(self, n),
            *constraints.ordering_constraint_2(self, n),
            *constraints.ordering_constraint_3(self, n),
            *constraints.optimized_ordering_constraint_4(self, n),
            *constraints.optimized_relationship_constraint(self)
        ]
    
    def decode_solution(self, solution):
        # Create a reverse map from value to key
        reverse_map = {v: k for k, v in self.variable_map.items()}
        
        # Collect all keys with positive values in the solution
        true_variables = [
            reverse_map[val] 
            for val in solution 
            if val > 0 and val in reverse_map
        ]
        
        return true_variables

    def solve_hamilton(self):

        solution = pycosat.solve(self.clauses)

        if solution == "UNSAT":
            return "No"

        # Decode the solution
        cycle = self.decode_solution(solution)

        return cycle
    
    def validate(self, solution):

        n = len(self.G)

        # Separate s_ij and o_ij variables
        s_array = [v for v in solution if v.startswith('s_')]
        o_array = [v for v in solution if v.startswith('o_')]

        # Step 1: Check if each vertex appears exactly once in s_array as both i and j
        s_counts = {}
        
        for s in s_array:
            i, j = int(s[2]), int(s[3])
            s_counts[i] = s_counts.get(i, 0) + 1
            s_counts[j] = s_counts.get(j, 0) + 1
        
        # Each vertex must appear exactly twice (once as a successor and once as a predecessor)
        for vertex in range(n):
            if s_counts.get(vertex, 0) != 2:
                return False
        
        # Step 2: Verify the ordering variables following the cycle
        visited = [False] * n
        current_vertex = 0
        
        for _ in range(n):
            # Find the successor of the current vertex
            successor = None
            for s in s_array:
                i, j = int(s[2]), int(s[3])
                if i == current_vertex:
                    successor = j
                    break
            
            if successor is None or visited[successor]:
                return False
            
            # Check the corresponding ordering variable o_ij
            o_var = f"o_{current_vertex}{successor}"
            if o_var not in o_array:
                return False
            
            visited[current_vertex] = True
            current_vertex = successor
        
        # The final step should loop back to the starting vertex (0)
        return current_vertex == 0


    
