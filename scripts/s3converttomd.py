import csv
import os
import re
import time
import requests
import json

# --- Configuration ---
CSV_FILE_PATH = 'candidatos.csv'
OUTPUT_FOLDER = 'mdata'

# --- OpenWebUI API Configuration ---
OPENWEBUI_API_URL = 'http://llm:3000/api/chat/completions'
OPENWEBUI_TOKEN = 'your_api_key_here'
OPENWEBUI_MODEL = "gemma3:27b"
API_TIMEOUT = 60

# --- Helper Functions (Keep sanitize_filename, format_heading, create_markdown_list, call_tagging_api, format_row_for_prompt, call_description_api) ---
# ... (Keep all helper functions exactly as they were in the previous version) ...
def sanitize_filename(filename):
    """Removes invalid characters for filenames and replaces spaces."""
    filename = re.sub(r'[^\w\s-]', '', filename).strip()
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename[:100]

def format_heading(header):
    """Formats CSV header into a Markdown H2 heading."""
    renames = {
        "PODER_POSTULA": "Poder que postula",
        "REDES": "Redes Sociales",
        "TRAYECTORIA_ACADEMICA": "Trayectoria Academica",
        "MOTIVO_CARGO_PUBLICO": "Motivo para buscar el Cargo Publico",
        "VISION_FUNCION_JURISDICCIONAL": "Vision sobre la Funcion Jurisdiccional",
        "VISION_IMPARTICION_JUSTICIA": "Vision sobre la Imparticion de Justicia",
        "PROPUESTA_1": "Propuesta 1",
        "PROPUESTA_2": "Propuesta 2",
        "PROPUESTA_3": "Propuesta 3",
    }
    if header in renames:
         return renames[header]
    else:
        return header.replace('_', ' ').title()

def create_markdown_list(data_string, separator):
    """Creates a Markdown bullet list from a string separated by a delimiter."""
    if not data_string or not data_string.strip():
        return "- *No especificado*"
    items = [item.strip() for item in data_string.split(separator) if item.strip()]
    if not items:
        return "- *No especificado*"
    return "\n".join([f"- {item}" for item in items])

def call_tagging_api(text_data, tag_type="generic"):
    """Calls the OpenWebUI API to generate TAGS for the given text data."""
    print(f"--- [API Call] Requesting {tag_type.upper()} Tags ---")
    if not text_data or not text_data.strip():
        print("--- [API Call] No text data for tags, skipping API call. ---")
        return []
    if "YOUR_OPENWEBUI_BEARER_TOKEN" in OPENWEBUI_TOKEN:
        print("--- [API Call SKIPPED] Token not configured. Returning example tags. ---")
        return [f"Tag_{tag_type.capitalize()}_Ejemplo1", f"Tag_{tag_type.capitalize()}_Ejemplo2"]

    context_description = "educación y trayectoria académica" if tag_type == "education" else "propósito, visión y propuestas"
    prompt = (
        f"Analiza el siguiente texto de un candidato relacionado con su {context_description}. "
        f"Extrae las palabras clave o conceptos más relevantes como etiquetas (tags). "
        f"Genera únicamente una lista de estas etiquetas separadas por comas, sin ninguna otra explicación, saludo o introducción. Asegúrate de que la salida sea solo 'tag1, tag2, tag3'. "
        f"Texto del candidato:\n```\n{text_data[:3500]}\n```"
    )
    headers = {'Authorization': f'Bearer {OPENWEBUI_TOKEN}', 'Content-Type': 'application/json'}
    data = {"model": OPENWEBUI_MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False}

    try:
        print(f"--- [API Call - Tags] Sending request to {OPENWEBUI_API_URL}...")
        response = requests.post(OPENWEBUI_API_URL, headers=headers, json=data, timeout=API_TIMEOUT / 2)
        response.raise_for_status()
        api_result = response.json()

        if 'choices' in api_result and len(api_result['choices']) > 0:
            message = api_result['choices'][0].get('message', {})
            content = message.get('content', '').strip()
            if content:
                tags_list = [tag.strip() for tag in content.split(',') if tag.strip()]
                tags_list = [re.sub(r'^\s*[-*"\']?\s*(.*?)\s*["\']?\s*$', r'\1', tag) for tag in tags_list if tag]
                print(f"--- [API Call - Tags] Received Tags: {tags_list} ---")
                return tags_list
            else:
                print("--- [API Call - Tags] Received empty content from API. ---")
                return []
        else:
            print(f"--- [API Call - Tags] Unexpected API response structure. Response: {api_result}")
            return []
    except requests.exceptions.Timeout:
        print(f"Error: API call for tags timed out.")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenWebUI API for tags: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred during tag API processing: {e}")
        return []

def format_row_for_prompt(row_data):
    """Formats the row data dictionary into a string suitable for the LLM prompt."""
    lines = []
    list_cols_comma_prompt = ['PODER_POSTULA', 'REDES']
    list_cols_dot_prompt = ['CURSOS', 'TRAYECTORIA_ACADEMICA']
    prompt_key_map = {
        "NOMBRE_CANDIDATO": "Nombre Candidato", "CARGO": "Cargo", "ENTIDAD": "Entidad",
        "SEXO": "Sexo", "TELEFONO": "Telefono", "CORREO_ELECTRONICO": "Correo Electronico",
        "NUM_LIST_EN_BOLETA": "Numero de lista en boleta", "PODER_POSTULA": "Poder que postula",
        "REDES": "Redes Sociales", "TRAYECTORIA_ACADEMICA": "Trayectoria Academica",
        "CURSOS": "Cursos", "MOTIVO_CARGO_PUBLICO": "Motivo para buscar el Cargo Publico",
        "VISION_FUNCION_JURISDICCIONAL": "Vision sobre la Funcion Jurisdiccional",
        "VISION_IMPARTICION_JUSTICIA": "Vision sobre la Imparticion de Justicia",
        "PROPUESTA_1": "Propuesta 1", "PROPUESTA_2": "Propuesta 2", "PROPUESTA_3": "Propuesta 3",
    }
    for header, value in row_data.items():
        value_str = str(value).strip() if value is not None else ""
        if not value_str: continue
        formatted_key = prompt_key_map.get(header, header.replace('_', ' ').title())
        if header in list_cols_comma_prompt:
            items = [item.strip() for item in value_str.split(',') if item.strip()]
            value_str = "; ".join(items) if items else "*No especificado*"
        elif header in list_cols_dot_prompt:
            items = [item.strip() for item in value_str.split('.') if item.strip()]
            value_str = "; ".join(items) if items else "*No especificado*"
        lines.append(f"- **{formatted_key}:** {value_str}")
    return "\n".join(lines)

def call_description_api(candidate_row):
    """Calls the OpenWebUI API to generate a DESCRIPTION for the candidate based on row data."""
    print(f"--- [API Call] Requesting DESCRIPTION ---")
    if not candidate_row:
        print("--- [API Call] No row data for description, skipping API call. ---")
        return None
    if "YOUR_OPENWEBUI_BEARER_TOKEN" in OPENWEBUI_TOKEN:
        print("--- [API Call SKIPPED] Token not configured. Returning example description. ---")
        return "Esta es una descripción de ejemplo generada porque el token de API no está configurado."

    formatted_data = format_row_for_prompt(candidate_row)
    if not formatted_data:
        print("--- [API Call] No relevant data found in row to generate description. ---")
        return None
    data_limit = 4000
    if len(formatted_data) > data_limit:
         print(f"--- [API Call - Warning] Truncating input data for description prompt to {data_limit} characters.")
         formatted_data = formatted_data[:data_limit] + "\n... (datos truncados)"

    prompt = (
        "Eres un asistente encargado de resumir perfiles de candidatos para una elección.\n"
        "Basándote estrictamente en los siguientes datos proporcionados sobre un candidato, genera una descripción concisa y objetiva de su perfil en uno o dos párrafos.\n"
        "Enfócate en su trayectoria, motivaciones y propuestas si están disponibles. No inventes información ni des opiniones.\n\n"
        "**Datos del Candidato:**\n"
        f"{formatted_data}\n\n"
        "**Descripción Generada:**"
    )
    headers = {'Authorization': f'Bearer {OPENWEBUI_TOKEN}', 'Content-Type': 'application/json'}
    data = {
        "model": OPENWEBUI_MODEL, "messages": [{"role": "user", "content": prompt}],
        "stream": False, "max_tokens": 300
    }
    try:
        print(f"--- [API Call - Description] Sending request to {OPENWEBUI_API_URL}...")
        response = requests.post(OPENWEBUI_API_URL, headers=headers, json=data, timeout=API_TIMEOUT)
        response.raise_for_status()
        api_result = response.json()
        if 'choices' in api_result and len(api_result['choices']) > 0:
            message = api_result['choices'][0].get('message', {})
            content = message.get('content', '').strip()
            if content:
                print(f"--- [API Call - Description] Received Description (first 100 chars): {content[:100]}... ---")
                content = re.sub(r'^\s*["\']?(.*?)\s*["\']?\s*$', r'\1', content)
                return content
            else:
                print("--- [API Call - Description] Received empty content from API. ---")
                return None
        else:
            print(f"--- [API Call - Description] Unexpected API response structure. Response: {api_result}")
            return None
    except requests.exceptions.Timeout:
        print(f"Error: API call for description timed out after {API_TIMEOUT} seconds.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenWebUI API for description: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during description API processing: {e}")
        return None

# --- Main Script ---
def process_candidates_csv():
    """Reads the CSV and generates markdown files for each candidate."""
    if not os.path.exists(OUTPUT_FOLDER):
        print(f"Creating output directory: {OUTPUT_FOLDER}")
        os.makedirs(OUTPUT_FOLDER)
    else:
        print(f"Output directory '{OUTPUT_FOLDER}' already exists.")

    if "YOUR_OPENWEBUI_BEARER_TOKEN" in OPENWEBUI_TOKEN:
        print("\n" + "="*50)
        print(" WARNING: OpenWebUI API token is set to the placeholder value!")
        print(" Please edit the script and set the 'OPENWEBUI_TOKEN' variable.")
        print(" API calls for Tags and Descriptions will be skipped/simulated.")
        print("="*50 + "\n")

    try:
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            if not reader.fieldnames:
                print(f"Error: CSV file '{CSV_FILE_PATH}' seems empty or has no headers.")
                return

            print(f"Processing candidates from: {CSV_FILE_PATH}")
            processed_count = 0
            skipped_count = 0

            # Define columns for specific processing
            proposal_cols = ['PROPUESTA_1', 'PROPUESTA_2', 'PROPUESTA_3']
            education_cols = ['CURSOS', 'TRAYECTORIA_ACADEMICA']
            purpose_text_gather_cols = ['MOTIVO_CARGO_PUBLICO', 'VISION_FUNCION_JURISDICCIONAL', 'VISION_IMPARTICION_JUSTICIA'] + proposal_cols
            list_cols_comma = ['PODER_POSTULA', 'REDES']
            list_cols_dot = ['CURSOS', 'TRAYECTORIA_ACADEMICA']
            metadata_columns = { # Columns for standard metadata
                'NOMBRE_CANDIDATO': 'Nombre Candidato', 'CARGO': 'Cargo',
                'ENTIDAD': 'Entidad', 'SEXO': 'Sexo',
                'TELEFONO': 'Telefono', 'CORREO_ELECTRONICO': 'Correo Electronico',
                'NUM_LISTA_EN_BOLETA': 'Numero de lista en boleta',
                'ESCOLARIDAD': 'Escolaridad','ESTATUS_ESCOLARIDAD': 'Estatus Escolaridad',
            }
            # Create a set of headers used ONLY for metadata or combined proposals
            # These should NOT get their own H2 section in the body
            skip_in_body_headers = set(metadata_columns.keys()) | set(proposal_cols)


            for i, row in enumerate(reader):
                print("-" * 40)
                print(f"Processing Row {i+1}...")

                candidate_name = row.get('NOMBRE_CANDIDATO', f'Candidato_{i+1}').strip()
                list_number = row.get('NUM_LIST_EN_BOLETA', str(i+1)).strip()

                if not candidate_name:
                    print(f"Warning: Skipping row {i+1} due to missing or empty 'NOMBRE_CANDIDATO'.")
                    skipped_count += 1
                    continue

                base_filename = f"{candidate_name}_{list_number}"
                safe_filename = sanitize_filename(base_filename) + '.md'
                output_filepath = os.path.join(OUTPUT_FOLDER, safe_filename)
                print(f"Generating file: {output_filepath}")

                # --- Step 1: Pre-collect Text for Tagging APIs ---
                education_text_parts = []
                purpose_text_parts = []
                for col in education_cols:
                    value = row.get(col, '').strip()
                    if value:
                        education_text_parts.append(value)
                for col in purpose_text_gather_cols: # Includes proposals here
                    value = row.get(col, '').strip()
                    if value:
                        purpose_text_parts.append(value)

                education_data_combined = " . ".join(education_text_parts)
                purpose_data_combined = " . ".join(purpose_text_parts)

                # --- Step 2: Call Tagging APIs EARLIER ---
                education_tags_list = call_tagging_api(education_data_combined, tag_type="education")
                purpose_tags_list = call_tagging_api(purpose_data_combined, tag_type="purpose")

                # --- Step 3: Format Tags for Metadata ---
                education_tags_meta_value = ", ".join(sorted(list(set(education_tags_list)))) if education_tags_list else "*No generado*"
                purpose_tags_meta_value = ", ".join(sorted(list(set(purpose_tags_list)))) if purpose_tags_list else "*No generado*"

                # --- Initialize Markdown Content list ---
                markdown_lines = []

                # --- Step 4 & 5: Generate METADATA Block (including Tags) ---
                metadata_block_lines = []
                for csv_header, meta_key in metadata_columns.items():
                    value = row.get(csv_header, '').strip()
                    metadata_block_lines.append(f"{meta_key}: {value if value else '*No especificado*'}")
                metadata_block_lines.append(f"Tags Educación: {education_tags_meta_value}")
                metadata_block_lines.append(f"Tags Propósito: {purpose_tags_meta_value}")

                markdown_lines.extend(metadata_block_lines)
                markdown_lines.append("\n") # Blank line after metadata

                # --- Step 6: Call API for DESCRIPTION ---
                candidate_description = call_description_api(row)
                if candidate_description:
                    markdown_lines.append("## Descripción del Candidato \n")
                    markdown_lines.append(candidate_description)
                    markdown_lines.append("\n")
                
                # --- Step 7: Process remaining columns for main body content ---
                for header, value in row.items():
                    # <<<--- MODIFIED SKIPPING LOGIC ---<<<
                    # Skip columns already used for metadata or combined proposals
                    if header in skip_in_body_headers:
                        continue
                    # --- End of Modified Skipping Logic ---
                    if header in ['ESTATUS']:
                        continue  # Skip 'ESTATUS' column
                    # Clean up value
                    value = value.strip() if value is not None else ""

                    # Add formatted content (H2 heading + value/list) to Markdown
                    formatted_header = format_heading(header)
                    markdown_lines.append(f"## {formatted_header}\n")

                    if header in list_cols_comma:
                        markdown_lines.append(create_markdown_list(value, ','))
                    elif header in list_cols_dot:
                         markdown_lines.append(create_markdown_list(value, '.'))
                    else:
                        markdown_lines.append(value if value else "*No especificado*")
                    markdown_lines.append("\n")

                # --- Step 8: Add combined Proposals section ---
                proposals_text_list = []
                has_proposals = False
                for p_col in proposal_cols:
                    p_value = row.get(p_col, "").strip()
                    if p_value:
                        has_proposals = True
                        proposals_text_list.append(p_value)
                if has_proposals:
                    markdown_lines.append("## Propuestas\n")
                    markdown_lines.append("\n".join([f"- {prop}" for prop in proposals_text_list]))
                    markdown_lines.append("\n")

                

                # --- Step 9: Write the Markdown file ---
                try:
                    with open(output_filepath, 'w', encoding='utf-8') as md_file:
                        md_content = "\n".join(markdown_lines)
                        md_file.write(md_content)
                    processed_count += 1
                except IOError as e:
                    print(f"Error writing file {output_filepath}: {e}")
                    skipped_count += 1
                except Exception as e:
                     print(f"An unexpected error occurred while writing {output_filepath}: {e}")
                     skipped_count += 1

            print("-" * 40)
            print(f"\nProcessing Complete.")
            print(f"Successfully generated {processed_count} markdown files in '{OUTPUT_FOLDER}'.")
            if skipped_count > 0:
                print(f"Skipped {skipped_count} rows due to errors or missing data.")

    except FileNotFoundError:
        print(f"Error: Input CSV file not found at '{CSV_FILE_PATH}'")
    except Exception as e:
        print(f"An unexpected error occurred during CSV processing: {e}")

# --- Run the script ---
if __name__ == "__main__":
    process_candidates_csv()