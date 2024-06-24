import random
import matplotlib.pyplot as plt

# Define the pay table
pay_table = {
    "reel_icon_1.png": 3,
    "reel_icon_2.png": 5,
    "reel_icon_3.png": 10,
    "reel_icon_4.png": 25,
    "reel_icon_5.png": 50,
    "reel_icon_6.png": 100,
    "reel_icon_7.png": 200
}

# Read the reel maps from files
def read_reel_map(filename):
    reel_map = []
    with open(filename, "r") as f:
        for line in f:
            _, icon = line.strip().split('=')
            reel_map.append(icon)
    return reel_map

reel1 = read_reel_map("reel1_icon_mapping.conf")
reel2 = read_reel_map("reel2_icon_mapping.conf")
reel3 = read_reel_map("reel3_icon_mapping.conf")

# Simulator parameters
starting_credits = 1000
num_spins = 1000

# Perform the spins and track credits
def simulate_spins(starting_credits, num_spins, reel1, reel2, reel3, pay_table):
    credits = starting_credits
    results = []
    
    for _ in range(num_spins):
        # Spin the reels
        i = random.randint(0, len(reel1) - 1)
        j = random.randint(0, len(reel2) - 1)
        k = random.randint(0, len(reel3) - 1)
        
        # Check for a win
        if reel1[i] == reel2[j] == reel3[k]:
            credits += pay_table[reel1[i]]
        credits -= 1  # Subtract the cost of the spin
        
        results.append(credits)
    
    return results

# Run the simulation
results = simulate_spins(starting_credits, num_spins, reel1, reel2, reel3, pay_table)

# Print the final credits
print(f"Final credits after {num_spins} spins: {results[-1]}")

# Save results to a file
with open("simulation_results.txt", "w") as f:
    for result in results:
        f.write(f"{result}\n")

# Plot the results
plt.plot(results)
plt.xlabel('Spin')
plt.ylabel('Credits')
plt.title('Credits Over Time')
plt.ylim(bottom=0)  # Set the bottom of the y-axis to 0
plt.show()
