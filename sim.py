import subprocess
import ast

# Define payout values
payouts = {
    'reel_icon_1.png': 3,
    'reel_icon_2.png': 5,
    'reel_icon_3.png': 10,
    'reel_icon_4.png': 25,
    'reel_icon_5.png': 50,
    'reel_icon_6.png': 100,
    'reel_icon_7.png': 200,
}

def run_reel_gen_script():
    # Run the three_reel_value_gen.py script and capture the output
    result = subprocess.run(
        ['python', 'three_reel_value_gen.py'],
        capture_output=True,
        text=True
    )
    try:
        # Assuming the script outputs a list of the reel results
        reel_results = ast.literal_eval(result.stdout.strip())
    except (ValueError, SyntaxError) as e:
        print(f"Error decoding output: {e}")
        print(f"Script output: {result.stdout.strip()}")
        reel_results = ['default_icon.png', 'default_icon.png', 'default_icon.png']
    return reel_results

def calculate_payout(results):
    if results[0] == results[1] == results[2]:
        return payouts.get(results[0], 0)
    return 0

def simulate_pulls(num_pulls, starting_credits):
    credits = starting_credits
    for spin_number in range(1, num_pulls + 1):
        if credits <= 0:
            print("Out of credits!")
            break
        credits -= 1  # Cost of one pull
        results = run_reel_gen_script()
        payout = calculate_payout(results)
        credits += payout
        print(f"Spin {spin_number}: Results: {results}, Payout: {payout}, Remaining Credits: {credits}")
    return credits

# Run the simulation
final_credits = simulate_pulls(10000, 1000)
print(f"Final Credits after 10000 pulls: {final_credits}")
