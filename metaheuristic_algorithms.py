import numpy as np
import random
from abc import ABC, abstractmethod

class MetaheuristicAlgorithm(ABC):
    """Base class for all metaheuristic load balancing algorithms"""
    def __init__(self, num_nodes, num_tasks):
        self.num_nodes = num_nodes
        self.num_tasks = num_tasks
        self.nodes = self.initialize_nodes()
        self.tasks = self.generate_tasks()
        self.fault_probability = 0.05
        self.min_nodes_for_operation = 3
        self.completed_tasks = 0

    def initialize_nodes(self):
        """Initialize VMs with realistic parameters"""
        return [{
            'id': i,
            'pe': 4,
            'mips': random.randint(2000, 4000),
            'capacity': 4 * random.randint(2000, 4000),
            'current_load': 0,
            'failed': False,
            'energy_coefficient': random.uniform(0.001, 0.003)
        } for i in range(self.num_nodes)]

    def generate_tasks(self):
        """Generate realistic cloud tasks"""
        return [{
            'id': i,
            'length': random.randint(200, 4000),
            'pe': 1,
            'mips_required': random.randint(200, 4000),
            'priority': random.choice([1, 2, 3])
        } for i in range(self.num_tasks)]

    @abstractmethod
    def allocate_task(self, task):
        pass

    def simulate_failure(self):
        """Safe failure simulation with limits"""
        active_nodes = [n for n in self.nodes if not n['failed']]
        if len(active_nodes) <= self.min_nodes_for_operation:
            return

        # Only allow up to 10% of nodes to fail
        max_failures = max(1, int(self.num_nodes * 0.1))
        current_failures = sum(1 for n in self.nodes if n['failed'])
        
        if current_failures >= max_failures:
            return

        # Select a random active node to fail
        node = random.choice(active_nodes)
        if random.random() < self.fault_probability:
            node['failed'] = True
            if node['current_load'] > 0:
                # Create a new task representing the failed workload
                temp_task = {
                    'id': -1,  # Special ID for migrated tasks
                    'mips_required': node['current_load'],
                    'length': node['current_load'],  # Approximate length
                    'pe': 1,
                    'priority': 1
                }
                if self.allocate_task(temp_task):
                    node['current_load'] = 0
                else:
                    # If couldn't migrate, count as lost workload
                    self.completed_tasks -= int(node['current_load'] / 1000)

    def run(self):
        """Execute simulation with safety checks"""
        self.completed_tasks = 0
        
        for task in self.tasks:
            if self.allocate_task(task):
                self.completed_tasks += 1
            
            # Periodically check for failures
            if random.random() < 0.1:  # 10% chance per task
                self.simulate_failure()
        
        return self.calculate_metrics()

    def calculate_metrics(self):
        """Calculate realistic metrics"""
        active_nodes = [n for n in self.nodes if not n['failed']]
        failed_nodes = [n for n in self.nodes if n['failed']]
        
        # Response Time Calculation
        response_times = []
        for node in active_nodes:
            if node['capacity'] > 0:
                utilization = min(1.0, node['current_load'] / node['capacity'])
                # Base 100ms + scaled processing delay
                response_time = 0.1 + (utilization * 0.9)
                response_times.append(response_time)
        
        # Throughput Calculation
        throughput = (self.completed_tasks / self.num_tasks) * 100 if self.num_tasks > 0 else 0
        
        # Fault Tolerance Calculation
        recovered_nodes = sum(1 for n in failed_nodes if n['current_load'] == 0)
        fault_tolerance = (recovered_nodes / len(failed_nodes)) * 100 if failed_nodes else 100
        
        # Energy Consumption
        energy = sum(
            n['current_load'] * n['energy_coefficient']
            for n in active_nodes
        )
        
        return {
            'avg_response_time': np.mean(response_times) if response_times else 0.5,
            'throughput': min(100.0, throughput),  # Cap at 100%
            'fault_tolerance': min(100.0, fault_tolerance),  # Cap at 100%
            'energy_consumption': energy,
            'active_nodes': len(active_nodes),
            'completed_tasks': self.completed_tasks
        }

class LionOptimizationLB(MetaheuristicAlgorithm):
    def __init__(self, num_nodes, num_tasks):
        super().__init__(num_nodes, num_tasks)
        self.pride_size = max(5, num_nodes // 4)
        self.territories = self._initialize_territories()
        self.nomads = []
        self.migration_threshold = 0.8

    def _initialize_territories(self):
        """Divide nodes into prides with safety checks"""
        territories = []
        for i in range(0, self.num_nodes, self.pride_size):
            territory_nodes = self.nodes[i:i+self.pride_size]
            if len(territory_nodes) >= 2:
                territories.append({
                    'nodes': territory_nodes,
                    'best_fitness': float('inf'),
                    'best_node': None
                })
        return territories or [{'nodes': self.nodes, 'best_fitness': float('inf'), 'best_node': None}]

    def _calculate_fitness(self, node):
        """Fitness function with failure check"""
        if node['failed'] or node['capacity'] <= 0:
            return float('inf')
        return (node['current_load'] / node['capacity']) * 100

    def _hunting_phase(self, task):
        """Coordinated hunting with population checks"""
        for territory in self.territories:
            active_nodes = [n for n in territory['nodes'] if not n['failed'] and n['capacity'] > 0]
            if len(active_nodes) < 2:
                continue
                
            if random.random() < 0.7:  # 70% exploitation probability
                num_hunters = max(2, min(len(active_nodes)//2, len(active_nodes)))
                hunters = random.sample(active_nodes, num_hunters)
                best_hunter = min(hunters, key=self._calculate_fitness)
                
                if (best_hunter['current_load'] + task['mips_required']) <= best_hunter['capacity']:
                    best_hunter['current_load'] += task['mips_required']
                    # Update territory best
                    current_fit = self._calculate_fitness(best_hunter)
                    if current_fit < territory['best_fitness']:
                        territory['best_fitness'] = current_fit
                        territory['best_node'] = best_hunter
                    return True
        return False

    def _nomad_phase(self, task):
        """Nomad migration with load checks"""
        if not self.nomads:
            active_nodes = [n for n in self.nodes if not n['failed'] and n['capacity'] > 0]
            if not active_nodes:
                return False
            self.nomads = sorted(
                active_nodes,
                key=self._calculate_fitness,
                reverse=True
            )[:max(2, self.num_nodes//10)]
        
        for nomad in self.nomads:
            if nomad['current_load'] > nomad['capacity'] * self.migration_threshold:
                active_nodes = [n for n in self.nodes if not n['failed'] and n['capacity'] > 0 and n != nomad]
                if not active_nodes:
                    continue
                    
                recipient = min(active_nodes, key=self._calculate_fitness)
                migratable = min(
                    nomad['current_load'] * 0.3,
                    task['mips_required'],
                    recipient['capacity'] - recipient['current_load']
                )
                if migratable > 0:
                    nomad['current_load'] -= migratable
                    recipient['current_load'] += migratable
                    return True
        return False

    def allocate_task(self, task):
        """Three-phase allocation with fallbacks"""
        # Phase 1: Pride hunting
        if self._hunting_phase(task):
            return True
        
        # Phase 2: Nomad migration
        if self._nomad_phase(task):
            return True
        
        # Phase 3: Global fallback
        active_nodes = [n for n in self.nodes if not n['failed'] and n['capacity'] > 0]
        if active_nodes:
            best_global = min(active_nodes, key=self._calculate_fitness)
            if (best_global['current_load'] + task['mips_required']) <= best_global['capacity']:
                best_global['current_load'] += task['mips_required']
                return True
        
        return False

class BatAlgorithm(MetaheuristicAlgorithm):
    def __init__(self, num_nodes, num_tasks):
        super().__init__(num_nodes, num_tasks)
        self.loudness = 0.5
        self.pulse_rate = 0.5

    def allocate_task(self, task):
        active_nodes = [n for n in self.nodes if not n['failed'] and n['capacity'] > 0]
        if not active_nodes:
            return False
            
        best_node = min(active_nodes, key=lambda n: n['current_load'] / n['capacity'])
        
        if random.random() > self.pulse_rate:
            candidate = random.choice(active_nodes)
            if (candidate['current_load'] + task['mips_required']) <= candidate['capacity']:
                candidate['current_load'] += task['mips_required']
                return True
        
        if (best_node['current_load'] + task['mips_required']) <= best_node['capacity']:
            best_node['current_load'] += task['mips_required']
            return True
        
        return False

class CrowSearchAlgorithm(MetaheuristicAlgorithm):
    def __init__(self, num_nodes, num_tasks):
        super().__init__(num_nodes, num_tasks)
        self.memory = [None] * num_nodes
        self.flight_length = 0.1

    def allocate_task(self, task):
        active_nodes = [n for n in self.nodes if not n['failed'] and n['capacity'] > 0]
        if not active_nodes:
            return False
            
        # Initialize memory if empty
        if not any(self.memory):
            self.memory = [{'node': n, 'load': n['current_load']} for n in active_nodes]
        
        # Update memory with current loads
        for i, node in enumerate(self.nodes):
            if node in active_nodes and self.memory[i]:
                self.memory[i]['load'] = node['current_load']
        
        # Find best node in memory
        valid_memories = [m for m in self.memory if m and not m['node']['failed'] and m['node']['capacity'] > 0]
        if not valid_memories:
            return False
            
        best_memory = min(valid_memories, key=lambda m: m['load'] / m['node']['capacity'])
        
        if (best_memory['node']['current_load'] + task['mips_required']) <= best_memory['node']['capacity']:
            best_memory['node']['current_load'] += task['mips_required']
            return True
        
        return False

class MonarchButterflyOptimization(MetaheuristicAlgorithm):
    def __init__(self, num_nodes, num_tasks):
        super().__init__(num_nodes, num_tasks)
        self.bar = 5.0

    def allocate_task(self, task):
        active_nodes = [n for n in self.nodes if not n['failed'] and n['capacity'] > 0]
        if not active_nodes:
            return False
            
        if random.random() < self.bar / (self.bar + 1):
            # Migration operator
            src = max(active_nodes, key=lambda n: n['current_load'] / n['capacity'])
            dst = min(active_nodes, key=lambda n: n['current_load'] / n['capacity'])
            if (dst['current_load'] + task['mips_required']) <= dst['capacity']:
                dst['current_load'] += task['mips_required']
                return True
        else:
            # Adjustment operator
            node = random.choice(active_nodes)
            if (node['current_load'] + task['mips_required']) <= node['capacity']:
                node['current_load'] += task['mips_required']
                return True
        
        return False