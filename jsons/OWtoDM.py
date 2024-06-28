import json

# Load OW.json
with open('OW.json', 'r') as file:
    ow_data = json.load(file)

# Initialize the DM data
dm_data = []

# Process each item in the OW data
for item in ow_data:
    inscription_id = item.get("id")
    name = item["meta"].get("name")
    win_value = "0"
    
    # Extract win value from attributes
    for attribute in item["meta"].get("attributes", []):
        if attribute.get("trait_type") == "win":
            win_value = attribute.get("value")
            break
    
    # Create new DM item
    dm_item = {
        "inscriptionId": inscription_id,
        "name": name,
        "attributes": {
            "Win": win_value
        }
    }
    
    # Append to DM data
    dm_data.append(dm_item)

# Save DM.json
with open('DM.json', 'w') as file:
    json.dump(dm_data, file, indent=4)

print("Conversion complete! DM.json has been created.")
