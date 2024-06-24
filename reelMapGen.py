import random
import time

# Define the pay table
pay_table = {
    1: 3,
    2: 5,
    3: 10,
    4: 25,
    5: 50,
    6: 100,
    7: 200
}

# Icon names mapping
icon_names = {
    1: "reel_icon_1.png",
    2: "reel_icon_2.png",
    3: "reel_icon_3.png",
    4: "reel_icon_4.png",
    5: "reel_icon_5.png",
    6: "reel_icon_6.png",
    7: "reel_icon_7.png",
}

# Total symbols on each reel
total_reel_symbols = 256

# Minimum counts to ensure all symbols are present
min_counts = {
    1: 75,
    2: 40,
    3: 20,
    4: 30,
    5: 60,
    6: 18,  # Update to have 16 of symbol 6
    7: 8
}

# Function to calculate RTP from a sample of combinations
def calculate_sampled_rtp(reel1, reel2, reel3, pay_table, sample_size=100000):
    total_payout = 0
    total_bets = 0
    for _ in range(sample_size):
        i = random.randint(0, len(reel1) - 1)
        j = random.randint(0, len(reel2) - 1)
        k = random.randint(0, len(reel3) - 1)
        total_bets += 1
        if reel1[i] == reel2[j] == reel3[k]:
            total_payout += pay_table[reel1[i]]
    rtp = (total_payout / total_bets) * 100
    return rtp

# Generate the reel map for each reel based on the current symbol map
def generate_reel_map(symbol_map, total_symbols):
    reel_map = symbol_map.copy()
    while len(reel_map) < total_symbols:
        reel_map.append(random.choice(symbol_map))
    random.shuffle(reel_map)
    return reel_map[:total_symbols]

# Adjust the weights dynamically based on the current RTP
def adjust_weights(symbol_map, current_rtp, target_rtp):
    adjustment_factor = 1 + (target_rtp - current_rtp) / 1000  # Adjusting the factor for finer control

    new_symbol_map = []

    symbol_counts = {symbol: symbol_map.count(symbol) for symbol in range(1, 8)}

    for symbol in range(1, 8):
        current_count = symbol_counts[symbol]
        if current_rtp < target_rtp:
            if symbol in [4, 5]:  # Increase symbols 4, 5
                new_count = int(current_count * adjustment_factor)
            elif symbol in [6, 7]:
                new_count = int(current_count * (adjustment_factor * 0.98))  # Decrease slightly to balance
            else:
                new_count = current_count
        else:
            if symbol in [6, 7]:  # Decrease higher payout symbols
                new_count = int(current_count * adjustment_factor)
            else:
                new_count = current_count

        # Ensure minimum counts are maintained and avoid reducing to zero
        new_count = max(new_count, min_counts[symbol])
        new_symbol_map.extend([symbol] * new_count)

    # Ensure the total number of symbols remains the same and maintain an even distribution
    while len(new_symbol_map) > total_reel_symbols:
        excess_symbol = random.choice(new_symbol_map)
        if new_symbol_map.count(excess_symbol) > min_counts[excess_symbol]:
            new_symbol_map.remove(excess_symbol)
    while len(new_symbol_map) < total_reel_symbols:
        new_symbol_map.append(random.choice([1, 2, 3, 4, 5]))

    return new_symbol_map

# Ensure each symbol is included at least a few times and properly initialize the symbol map
def initialize_symbol_map():
    initial_map = []
    initial_map.extend([1] * 75)  # Common
    initial_map.extend([2] * 40)  # Common
    initial_map.extend([3] * 30)  # Common
    initial_map.extend([4] * 30)  # More frequent
    initial_map.extend([5] * 60)  # More frequent
    initial_map.extend([6] * 18)  # Updated to have 16 of symbol 6
    initial_map.extend([7] * 8)   # Rare

    return initial_map

# Generate the reel map ensuring all symbols are included multiple times
def generate_complete_reel_map(symbol_map, total_symbols):
    reel_map = symbol_map[:]
    required_symbols = set(range(1, 8))
    while len(reel_map) < total_symbols:
        reel_map.append(random.choice(symbol_map))
    random.shuffle(reel_map)

    # Ensure every required symbol is present multiple times
    for symbol in required_symbols:
        if reel_map.count(symbol) < min_counts[symbol]:
            for _ in range(min_counts[symbol] - reel_map.count(symbol)):
                replacement_index = random.randint(0, total_symbols - 1)
                reel_map[replacement_index] = symbol

    return reel_map

# Adjust reel maps to target 90% RTP with progress indicator, changing one reel at a time
def adjust_reel_maps_for_rtp(target_rtp, tolerance=2, sample_size=100000):
    iteration = 0
    start_time = time.time()
    symbol_map1 = initialize_symbol_map()
    symbol_map2 = initialize_symbol_map()
    symbol_map3 = initialize_symbol_map()
    reel_maps = [symbol_map1, symbol_map2, symbol_map3]
    reel_index = 0

    while True:
        iteration += 1
        reel1 = generate_complete_reel_map(symbol_map1, total_reel_symbols)
        reel2 = generate_complete_reel_map(symbol_map2, total_reel_symbols)
        reel3 = generate_complete_reel_map(symbol_map3, total_reel_symbols)

        current_rtp = calculate_sampled_rtp(reel1, reel2, reel3, pay_table, sample_size)
        elapsed_time = time.time() - start_time
        print(f"Iteration: {iteration}, Current RTP: {current_rtp:.2f}%, Elapsed Time: {elapsed_time:.2f}s")

        if abs(current_rtp - target_rtp) <= tolerance:  # Allow a tolerance of 2%
            return reel1, reel2, reel3

        # Adjust the weights for the current reel
        reel_maps[reel_index] = adjust_weights(reel_maps[reel_index], current_rtp, target_rtp)

        # Cycle to the next reel map
        reel_index = (reel_index + 1) % 3

        # Update the symbol maps
        symbol_map1, symbol_map2, symbol_map3 = reel_maps

        # Debug: print symbol counts for each reel
        print(f"Reel {reel_index + 1} symbol counts:")
        for symbol in range(1, 8):
            count = reel_maps[reel_index].count(symbol)
            print(f"Symbol {symbol}: {count}")

target_rtp = 85.0
tolerance = 0.5
sample_size = 100000
reel1, reel2, reel3 = adjust_reel_maps_for_rtp(target_rtp, tolerance, sample_size)

# Convert reel maps to icon names
reel1_icons = [icon_names[symbol] for symbol in reel1]
reel2_icons = [icon_names[symbol] for symbol in reel2]
reel3_icons = [icon_names[symbol] for symbol in reel3]

# Save reel maps to files
with open("reel1_icon_mapping.conf", "w") as f:
    for index, icon in enumerate(reel1_icons):
        f.write(f"{index:02x}={icon}\n")

with open("reel2_icon_mapping.conf", "w") as f:
    for index, icon in enumerate(reel2_icons):
        f.write(f"{index:02x}={icon}\n")

with open("reel3_icon_mapping.conf", "w") as f:
    for index, icon in enumerate(reel3_icons):
        f.write(f"{index:02x}={icon}\n")

# Print confirmation
print("Reel maps generated and saved successfully.")
