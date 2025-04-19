def _wrapped_invoke(state_dict: Dict) -> Dict:
        image_urls = state_dict.get("product_image_urls", [])
        product_name = state_dict.get("product_name", "Unknown Product") # Get product name from state
        descriptions_list = []

        print(f"--- Analyzing {len(image_urls)} image(s) for '{product_name}' ---")
        for url in image_urls:
            # Call the core logic for each image
            desc_obj = invoke_single_image_analysis(llm, url, product_name)
            if desc_obj: # Only append if analysis was successful
                # Convert Pydantic object to dict for state compatibility
                descriptions_list.append(desc_obj.model_dump())

        # Return the result in a dictionary format suitable for updating the state
        return {"product_image_descriptions": descriptions_list}