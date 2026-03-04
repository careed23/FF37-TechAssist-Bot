#!/usr/bin/env python3

import os
import re
import yaml
import logging
from unidecode import unidecode # Add this import
from docx import Document

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s') # Add this line for basic logging config
logger = logging.getLogger(__name__)

def slugify(text):
    text = unidecode(text).lower() # Use unidecode
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text

def parse_docx(docx_path):
    document = Document(docx_path)
    flows = []
    solutions = []

    current_flow = None
    current_step = None

    # Generate a base ID from the document filename
    base_id = slugify(os.path.basename(docx_path).replace(".docx", ""))
    flow_counter = 0
    step_counter = 0
    solution_counter = 0

    processed_paragraphs_with_index = []
    for idx, paragraph in enumerate(document.paragraphs):
        text = paragraph.text.strip()
        if text: # Only add non-empty paragraphs
            processed_paragraphs_with_index.append({
                "index": idx,
                "paragraph": paragraph,
                "text": text,
                "style": paragraph.style.name
            })

    for idx, p_info in enumerate(processed_paragraphs_with_index):
        text = p_info["text"]
        style = p_info["style"]
        original_paragraph_index = p_info["index"]

        if style.startswith("Heading 1"):
            flow_counter += 1
            flow_id = f"{base_id}_flow{flow_counter}"
            current_flow = {
                "id": flow_id,
                "name": text,
                "description": "",
                "steps": []
            }
            flows.append(current_flow)
            current_step = None

            desc_text = []
            for j in range(idx + 1, len(processed_paragraphs_with_index)):
                next_p_info = processed_paragraphs_with_index[j]
                if not next_p_info["text"]:
                    continue
                if not next_p_info["style"].startswith("Heading") and \
                   next_p_info["style"] != "List Paragraph":
                    desc_text.append(next_p_info["text"])
                    if len(desc_text) >= 3 or (j + 1 < len(processed_paragraphs_with_index) and \
                       (processed_paragraphs_with_index[j+1]["style"].startswith("Heading") or \
                        processed_paragraphs_with_index[j+1]["style"] == "List Paragraph")):
                        break
                else:
                    break

            if desc_text:
                current_flow["description"] = " ".join(desc_text)


        elif current_flow and style.startswith("Heading "):
            step_counter += 1
            step_id = f"{base_id}_step{step_counter}"
            current_step = {
                "id": step_id,
                "question": text,
                "options": []
            }
            current_flow["steps"].append(current_step)
        elif current_step and style == "List Paragraph":
            option_value = slugify(text)
            current_step["options"].append({
                "value": option_value,
                "description": text,
                "next": None,
                "original_paragraph_index": original_paragraph_index
            })

    # Collect all step IDs and their associated content for easier linking
    step_id_map = {}
    for flow in flows:
        for step in flow["steps"]:
            # Store original question and slugified question for lookup
            step_id_map[slugify(step["question"])] = step["id"]
            step_id_map[step["question"].lower()] = step["id"]
            
            # Also store just the numbers if present in the step question, e.g., "Step 1" -> 1
            num_match = re.search(r"(?:step|section)\s*(\d+)", step["question"], re.IGNORECASE)
            if num_match:
                step_id_map[f"step_{num_match.group(1)}"] = step["id"]
                step_id_map[f"section_{num_match.group(1)}"] = step["id"]


    # Second pass to link options to the next logical step or create solutions
    for flow in flows:
        for i, step in enumerate(flow["steps"]):
            for option in step["options"]:
                explicit_link_found = False
                
                # Try to parse explicit links first: "Go to Step X", "Refer to Section Y"
                explicit_link_pattern = r"(?:Go to|Refer to)\s+(?:Step|Section)\s+([\w\s-]+)"
                match = re.search(explicit_link_pattern, option["description"], re.IGNORECASE)
                if match:
                    target_text = match.group(1).strip()
                    
                    # Attempt to find a match in the step_id_map
                    # 1. Direct lowercased match
                    if target_text.lower() in step_id_map:
                        option["next"] = step_id_map[target_text.lower()]
                        explicit_link_found = True
                    # 2. Slugified match
                    elif slugify(target_text) in step_id_map:
                        option["next"] = step_id_map[slugify(target_text)]
                        explicit_link_found = True
                    # 3. Match with "Step X" or "Section Y" format (using numbers)
                    else:
                        num_match = re.search(r"(\d+)", target_text)
                        if num_match:
                            target_num = num_match.group(1)
                            if f"step_{target_num}" in step_id_map:
                                option["next"] = step_id_map[f"step_{target_num}"]
                                explicit_link_found = True
                            elif f"section_{target_num}" in step_id_map:
                                option["next"] = step_id_map[f"section_{target_num}"]
                                explicit_link_found = True
                                
                if explicit_link_found:
                    continue # Skip simple linking if explicit link was found

                # Simple linking: try to link to the next step in the flow (original logic)
                next_step_index = flow["steps"].index(step) + 1
                if next_step_index < len(flow["steps"]):
                    option["next"] = flow["steps"][next_step_index]["id"]
                else:
                    # If no next step, create a generic solution, but now try to make it more descriptive
                    solution_counter += 1
                    solution_id = f"{base_id}_sol{solution_counter}"
                    option["solution"] = solution_id

                    solution_title = f"Solution for {option["description"]}"
                    solution_steps_content = [f"Implement action for {option["description"]}"]

                    # Attempt to extract more meaningful solution title and steps
                    # Start looking for content immediately after the option's paragraph
                    option_p_idx_in_processed = -1
                    for temp_idx, p_info in enumerate(processed_paragraphs_with_index):
                        if p_info["index"] == option["original_paragraph_index"]:
                            option_p_idx_in_processed = temp_idx
                            break

                    if option_p_idx_in_processed != -1:
                        # Look for paragraphs immediately following the option's paragraph
                        extracted_solution_lines = []
                        for k in range(option_p_idx_in_processed + 1, len(processed_paragraphs_with_index)):
                            next_p_info = processed_paragraphs_with_index[k]
                            if not next_p_info["text"]:
                                continue
                            # Stop if we hit another heading or a list, or an empty line (already filtered)
                            if next_p_info["style"].startswith("Heading") or \
                               next_p_info["style"] == "List Paragraph":
                                break
                            extracted_solution_lines.append(next_p_info["text"])
                            if len(extracted_solution_lines) >= 5: # Limit description length
                                break

                        if extracted_solution_lines:
                            # Use the first line as a potential title, and the rest as steps
                            solution_title = extracted_solution_lines[0]
                            solution_steps_content = extracted_solution_lines

                    solutions.append({
                        "id": solution_id,
                        "title": solution_title,
                        "steps": solution_steps_content
                    })
                    if 'next' in option:
                        del option["next"]
                    del option["original_paragraph_index"]

    return flows, solutions

def main():
    data_dir = "../data"
    output_file = "../data/generated_flows.yaml"

    all_flows = []
    all_solutions = []

    for filename in os.listdir(data_dir):
        if filename.endswith(".docx"):
            docx_path = os.path.join(data_dir, filename)
            logger.info(f"Processing {docx_path}")
            flows, solutions = parse_docx(docx_path)
            all_flows.extend(flows)
            all_solutions.extend(solutions)

    output_data = {
        "flows": all_flows,
        "solutions": all_solutions
    }

    with open(output_file, "w") as f:
        yaml.dump(output_data, f, indent=2, sort_keys=False)
    logger.info(f"Generated YAML written to {output_file}")

if __name__ == "__main__":
    main()
