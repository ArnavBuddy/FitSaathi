from typing import List, Dict, Any

def rank_items(items: List[Dict[str, Any]], body_data: Dict[str, Any], user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
    ranked_items = []
    
    body_type = body_data.get("body_type")
    measurements = body_data.get("estimated_measurements", {})
    style_prefs = user_preferences.get("style_preferences", [])
    liked_items = user_preferences.get("liked_items", [])
    budget = user_preferences.get("budget_inr", {"min": 0, "max": 10000})

    for item in items:
        score = 0
        
        # 1. body_type_match: 30 points
        if body_type in item.get("body_types_suited", []):
            score += 30
        
        # 2. measurement_fit: 30 points
        # Simplified: Check if any size matches the waist/chest range
        best_size = "M" # Default
        fit_found = False
        for size, chart in item.get("fit_chart", {}).items():
            # Check chest
            item_chest = chart.get("chest_cm", [0, 0])
            user_chest = measurements.get("chest_cm_range", [0, 0])
            user_chest_avg = sum(user_chest) / 2 if user_chest else 0
            
            if item_chest[0] <= user_chest_avg <= item_chest[1]:
                best_size = size
                fit_found = True
                break
        
        if fit_found:
            score += 30
        
        # 3. style_tag_overlap: 20 points
        overlap = set(item.get("style_tags", [])).intersection(set(style_prefs))
        if style_prefs:
            score += (len(overlap) / len(style_prefs)) * 20
        
        # 4. preference_bonus: 10 points
        if item.get("item_id") in liked_items:
            score += 10
            
        # 5. stock_bonus: 5 points
        if item.get("stock_count", 0) > 20:
            score += 5
            
        # 6. price_fit: 5 points
        if budget["min"] <= item.get("price_inr", 0) <= budget["max"]:
            score += 5

        item["fit_score"] = round(score, 1)
        item["size_recommendation"] = best_size
        
        # Why it fits template
        fit_type = item.get("fit_type", "regular")
        subcategory = item.get("subcategory", "item")
        key_feature = "structured cut" if fit_type == "slim" else "relaxed silhouette"
        body_attribute = "proportions"
        
        item["why_it_fits"] = f"This {fit_type} {subcategory} suits your {body_type} frame — the {key_feature} works with your {body_attribute}."
        
        ranked_items.append(item)

    # Sort by fit_score desc
    ranked_items.sort(key=lambda x: x["fit_score"], reverse=True)
    return ranked_items
