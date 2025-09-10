import matplotlib.pyplot as plt
from metaheuristic_algorithms import (
    LionOptimizationLB,
    BatAlgorithm,
    CrowSearchAlgorithm,
    MonarchButterflyOptimization
)

def plot_comparison(results, num_nodes, num_tasks, filename_suffix=""):
    """Plot comparison graphs for the results"""
    try:
        plt.style.use('seaborn-v0_8')
    except:
        plt.style.use('ggplot')
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f"Load Balancing Algorithm Comparison\n({num_nodes} Nodes, {num_tasks} Tasks)", 
                y=1.02, fontsize=14)
    
    colors = ['#4C72B0', '#55A868', '#C44E52', '#8172B2']
    algorithms = list(results.keys())
    
    # Response Time Comparison
    bars1 = ax1.bar(algorithms, [res['avg_response_time'] for res in results.values()], color=colors)
    ax1.set_title("Response Time (seconds)\nLower is better", pad=15)
    ax1.set_ylabel("Seconds")
    ax1.set_ylim(0, 1.2)
    ax1.bar_label(bars1, fmt='%.2f', padding=3, fontsize=9)
    ax1.tick_params(axis='x', rotation=45)
    
    # Throughput Comparison
    bars2 = ax2.bar(algorithms, [res['throughput'] for res in results.values()], color=colors)
    ax2.set_title("Throughput (% tasks completed)\nHigher is better", pad=15)
    ax2.set_ylabel("Percentage")
    ax2.set_ylim(0, 110)
    ax2.bar_label(bars2, fmt='%.1f%%', padding=3, fontsize=9)
    ax2.tick_params(axis='x', rotation=45)
    
    # Fault Tolerance Comparison
    bars3 = ax3.bar(algorithms, [res['fault_tolerance'] for res in results.values()], color=colors)
    ax3.set_title("Fault Tolerance (% recovered)\nHigher is better", pad=15)
    ax3.set_ylabel("Percentage")
    ax3.set_ylim(0, 110)
    ax3.bar_label(bars3, fmt='%.1f%%', padding=3, fontsize=9)
    ax3.tick_params(axis='x', rotation=45)
    
    # Energy Consumption Comparison
    bars4 = ax4.bar(algorithms, [res['energy_consumption'] for res in results.values()], color=colors)
    ax4.set_title("Energy Consumption (kWh)\nLower is better", pad=15)
    ax4.set_ylabel("Kilowatt-hours")
    ax4.bar_label(bars4, fmt='%.1f', padding=3, fontsize=9)
    ax4.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    output_filename = f"algorithm_comparison_{filename_suffix}.png" if filename_suffix else "algorithm_comparison.png"
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_filename

def run_comparison(num_nodes=60, num_tasks=1000):
    """Run comparison with 4 algorithms"""
    algorithms = {
        "Lion Optimization": LionOptimizationLB(num_nodes, num_tasks),
        "Bat Algorithm": BatAlgorithm(num_nodes, num_tasks),
        "Crow Search": CrowSearchAlgorithm(num_nodes, num_tasks),
        "Monarch Butterfly": MonarchButterflyOptimization(num_nodes, num_tasks)
    }
    
    print(f"\nRunning performance comparison with {num_nodes} nodes and {num_tasks} tasks...")
    results = {}
    
    for name, algo in algorithms.items():
        print(f"\nExecuting {name}...")
        try:
            results[name] = algo.run()
            print(f"{name} results:")
            print(f"- Avg Response Time: {results[name]['avg_response_time']:.2f}s")
            print(f"- Throughput: {results[name]['throughput']:.1f}%")
            print(f"- Fault Tolerance: {results[name]['fault_tolerance']:.1f}%")
            print(f"- Energy Used: {results[name]['energy_consumption']:.2f}kWh")
            print(f"- Active Nodes: {results[name]['active_nodes']}/{num_nodes}")
            print(f"- Completed Tasks: {results[name]['completed_tasks']}/{num_tasks}")
        except Exception as e:
            print(f"Error running {name}: {str(e)}")
            results[name] = {
                'avg_response_time': 1.0,
                'throughput': 0.0,
                'fault_tolerance': 0.0,
                'energy_consumption': 0.0,
                'active_nodes': 0,
                'completed_tasks': 0
            }
    
    # Generate graphs
    suffix = f"{num_nodes}n_{num_tasks}t"
    graph_filename = plot_comparison(results, num_nodes, num_tasks, suffix)
    print(f"\nComparison graphs saved to '{graph_filename}'")
    
    # Print summary table
    print("\nPerformance Summary:")
    print(f"{'Algorithm':<20} | {'Response(s)':<10} | {'Throughput%':<10} | {'Fault%':<8} | {'Energy(kWh)':<12} | {'Completed'}")
    print("-" * 85)
    for name, res in results.items():
        print(f"{name:<20} | {res['avg_response_time']:>9.2f} | {res['throughput']:>9.1f}% | "
              f"{res['fault_tolerance']:>6.1f}% | {res['energy_consumption']:>11.2f} | "
              f"{res['completed_tasks']:>4}/{num_tasks}")

if __name__ == "__main__":
    # First run with paper's parameters
    run_comparison(num_nodes=60, num_tasks=1000)
    
    # Then run with smaller test case
    run_comparison(num_nodes=20, num_tasks=200)