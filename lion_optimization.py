import numpy as np
import random

class LionOptimizationLB:
    def __init__(self, num_nodes, num_tasks, max_iter=150):
        self.num_nodes = num_nodes
        self.num_tasks = num_tasks
        self.max_iter = max_iter
        self.nodes = self.initialize_nodes()
        self.tasks = self.generate_tasks()
        
    def initialize_nodes(self):
        """Initialize cloud nodes with random capacities"""
        nodes = []
        for i in range(self.num_nodes):
            # Each node has processing elements (PE) and MIPS capacity
            pe = 4  # Processing elements per node (from paper)
            mips = random.randint(2000, 4000)  # MIPS capacity (from paper)
            capacity = pe * mips  # Eq. 4 from paper
            nodes.append({
                'id': i,
                'pe': pe,
                'mips': mips,
                'capacity': capacity,
                'current_load': 0,
                'tasks': []
            })
        return nodes
    
    def generate_tasks(self):
        """Generate tasks with random lengths"""
        tasks = []
        for i in range(self.num_tasks):
            task_length = random.randint(200, 4000)  # Cloudlet length from paper
            pe_required = 1  # Assuming each task requires 1 PE
            tasks.append({
                'id': i,
                'length': task_length,
                'pe': pe_required,
                'mips_required': task_length * pe_required  # Simplified calculation
            })
        return tasks
    
    def fitness_function(self, node):
        """Calculate fitness of a node (Eq. 2 from paper)"""
        # Fitness is inversely proportional to current load
        # Higher fitness means better candidate for task allocation
        if node['capacity'] == 0:
            return 0
        return (1 - (node['current_load'] / node['capacity'])) * 100
    
    def identify_underutilized_node(self):
        """Identify underutilized node using Lion Optimization approach"""
        # Step 1: Calculate fitness for all nodes
        fitness_values = [self.fitness_function(node) for node in self.nodes]
        
        # Step 2: Find the node with highest fitness (underutilized)
        best_node_idx = np.argmax(fitness_values)
        best_node = self.nodes[best_node_idx]
        best_fitness = fitness_values[best_node_idx]
        
        # Step 3: Find neighbors (left and right in the list)
        left_neighbor = self.nodes[best_node_idx - 1] if best_node_idx > 0 else None
        right_neighbor = self.nodes[best_node_idx + 1] if best_node_idx < len(self.nodes) - 1 else None
        
        return best_node, left_neighbor, right_neighbor, best_fitness
    
    def update_node_positions(self, node, left_neighbor, right_neighbor):
        """Update neighboring nodes positions (Eq. 7 & 8 from paper)"""
        # Simplified implementation - in real scenario this would involve more complex calculations
        if left_neighbor:
            left_neighbor['current_load'] = max(0, left_neighbor['current_load'] - 
                                              random.uniform(0, 0.1) * left_neighbor['current_load'])
        if right_neighbor:
            right_neighbor['current_load'] = max(0, right_neighbor['current_load'] - 
                                           random.uniform(0, 0.1) * right_neighbor['current_load'])
        return left_neighbor, right_neighbor
    
    def allocate_task(self, task):
        """Allocate a task to a node using Lion Optimization"""
        # Identify underutilized node and neighbors
        best_node, left_neighbor, right_neighbor, fitness = self.identify_underutilized_node()
        
        # Check if best node can handle the task
        if (best_node['current_load'] + task['mips_required']) <= best_node['capacity']:
            best_node['current_load'] += task['mips_required']
            best_node['tasks'].append(task['id'])
            return best_node['id']
        else:
            # If best node is overloaded, try neighbors (migration)
            for neighbor in [left_neighbor, right_neighbor]:
                if neighbor and (neighbor['current_load'] + task['mips_required']) <= neighbor['capacity']:
                    neighbor['current_load'] += task['mips_required']
                    neighbor['tasks'].append(task['id'])
                    # Update positions (simulating hunting behavior)
                    self.update_node_positions(best_node, left_neighbor, right_neighbor)
                    return neighbor['id']
        
        # If no suitable node found, return -1 (shouldn't happen with proper load balancing)
        return -1
    
    def run_optimization(self):
        """Run the Lion Optimization load balancing algorithm"""
        allocation_results = []
        migration_count = 0
        
        for task in self.tasks:
            allocated_node = self.allocate_task(task)
            if allocated_node == -1:
                print(f"Warning: Task {task['id']} could not be allocated")
            allocation_results.append(allocated_node)
            
            # Simulate occasional node failures (for fault tolerance testing)
            if random.random() < 0.05:  # 5% chance of node failure
                failed_node_idx = random.randint(0, self.num_nodes - 1)
                print(f"Node {failed_node_idx} failed! Migrating tasks...")
                # Migrate tasks from failed node to others
                for t in self.nodes[failed_node_idx]['tasks']:
                    reallocated_node = self.allocate_task(self.tasks[t])
                    if reallocated_node != -1:
                        migration_count += 1
                self.nodes[failed_node_idx]['current_load'] = 0
                self.nodes[failed_node_idx]['tasks'] = []
        
        return allocation_results, migration_count
    
    def calculate_metrics(self):
        """Calculate performance metrics"""
        response_times = []
        throughput = 0
        total_capacity = sum(node['capacity'] for node in self.nodes)
        total_utilized = sum(node['current_load'] for node in self.nodes)
        
        # Simplified response time calculation
        for node in self.nodes:
            if node['tasks']:
                rt = (node['current_load'] / node['capacity']) * 0.5  # Scaling factor
                response_times.append(rt)
        
        avg_response_time = np.mean(response_times) if response_times else 0
        throughput = (total_utilized / total_capacity) * 100 if total_capacity > 0 else 0
        
        return {
            'avg_response_time': avg_response_time,
            'throughput': throughput,
            'load_distribution': [node['current_load']/node['capacity'] for node in self.nodes if node['capacity'] > 0]
        }