import json

def get_keyboard_data(directions):
    with open('keyboardOwn.json', 'r') as file:
        data = json.load(file)

    current_node = data["center"]

    try:
        for direction in directions:
            if direction in current_node:
                current_node = current_node[direction]
            else:
                return 'Error0', 'Wrong directions'

        # Fetch image and letter data from the final node
        image_url = current_node["image_url"]
        letter = current_node["letter"]

        # Construct the full image path
        full_image_path = data["imageLibrary"] + image_url if image_url != "none" else image_url

        return letter, full_image_path
    except Exception as e:
        # Handle any exceptions that arise (like incorrect JSON paths)
        return f"Error: {str(e)}", "No image available"
