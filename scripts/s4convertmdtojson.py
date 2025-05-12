import os
import json
import re

# --- Configuration ---
SOURCE_FOLDER = "done"
DESTINATION_FOLDER = "jdata"
METADATA_SEPARATOR = "## Descripción del Candidato"
SECTION_SEPARATOR_PATTERN = r"\n## " # Pattern to split sections

# --- Key Mapping (Spanish from Markdown to desired JSON key) ---
# Specific renames requested take precedence. Others are translated/transformed.
'''KEY_MAPPING = {
    # Specific renames requested
    "Nombre Candidato": "name",
    "Descripción del Candidato": "description", # Keeping accent as requested initially? No, description is better.
    # Correcting based on user request "descripcion del candidato to'descripción'" -> using 'descripcion'
    # Correcting based on user request "poder que postula" to "Poder_postulante" -> Using 'Poder_postulante'
    "Poder que postula": "proposed by",
    # General Metadata Fields (English, lowercase, underscore)
    "Cargo": "position",
    "Entidad": "entity",
    "Sexo": "gender",
    "Telefono": "phone",
    "Correo Electronico": "email",
    "Numero de lista en boleta": "ballot_list_number",
    "Escolaridad": "education_level",
    "Estatus Escolaridad": "education_status",
    "Tags Educación": "education_tags",
    "Tags Propósito": "purpose_tags",

    # General Section Headers (English, lowercase, underscore)
    # "Descripción del Candidato" is handled separately now, mapped above
    "Pagina Web": "website",
    "Redes Sociales": "social_media",
    "Cursos": "courses",
    "Curriculum Vitae": "cv_link",
    "Trayectoria Academica": "academic_background",
    "Motivo para buscar el Cargo Publico": "reason_for_seeking_office",
    "Vision sobre la Funcion Jurisdiccional": "vision_jurisdictional_function",
    "Vision sobre la Imparticion de Justicia": "vision_justice_delivery",
    "Propuestas": "proposals",
}
'''
KEY_MAPPING = {
    "Nombre Candidato": "Nombre",
    "Descripción del Candidato": "Descripcion", # Keeping accent as requested initially? No, description is better.
    # Correcting based on user request "descripcion del candidato to'descripción'" -> using 'descripcion'
    # Correcting based on user request "poder que postula" to "Poder_postulante" -> Using 'Poder_postulante'
    "Poder que postula": "Propuesto por",
    # General Metadata Fields (English, lowercase, underscore)
    "Cargo": "Cargo",
    "Entidad": "Entidad",
    "Sexo": "Sexo",
    "Telefono": "Telefono",
    "Correo Electronico": "Xorreo_electronico",
    "Numero de lista en boleta": "Numero_lista_boleta",
    "Escolaridad": "Nivel_escolaridad",
    "Estatus Escolaridad": "Estatus_escolaridad",
    "Tags Educación": "Tags_educacion",
    "Tags Propósito": "Tags_proposito",

    # General Section Headers (English, lowercase, underscore)
    # "Descripción del Candidato" is handled separately now, mapped above
    "Pagina Web": "Pagina_web",
    "Redes Sociales": "Redes_sociales",
    "Cursos": "Cursos",
    "Curriculum Vitae": "Curriculum_vitae",
    "Trayectoria Academica": "Trayectoria_academica",
    "Motivo para buscar el Cargo Publico": "Motivo_buscar_cargo_publico",
    "Vision sobre la Funcion Jurisdiccional": "Vision_funcion_jurisdiccional",
    "Vision sobre la Imparticion de Justicia": "Vision_imparticion_justicia",
    "Propuestas": "Propuestas",
}    
# --- Helper Functions ---

def clean_text(text):
    """Removes leading/trailing whitespace from text."""
    return text.strip() if text else ""

def transform_fallback_key(key):
    """Transforms a key if not found in mapping (lowercase, underscore)."""
    return key.lower().replace(' ', '_')

def get_mapped_key(original_key):
    """Gets the mapped key or provides a transformed fallback."""
    mapped = KEY_MAPPING.get(original_key)
    if mapped:
        return mapped
    else:
        fallback_key = transform_fallback_key(original_key)
        print(f"  Warning: Key '{original_key}' not found in KEY_MAPPING. Using fallback '{fallback_key}'.")
        return fallback_key

def parse_metadata(lines):
    """Parses the initial metadata lines into a dictionary using mapped keys."""
    metadata = {}
    for line in lines:
        line = clean_text(line)
        if not line:
            continue
        if ':' in line:
            key, value = line.split(':', 1)
            original_key = clean_text(key)
            json_key = get_mapped_key(original_key)
            value = clean_text(value)

            # Handle comma-separated tags specifically using the original key for identification
            if original_key.startswith("Tags"):
                metadata[json_key] = [tag.strip() for tag in value.split(',') if tag.strip()]
            else:
                metadata[json_key] = value
        else:
            # print(f"Warning: Metadata line without colon ignored: {line}")
            pass
    return metadata

def parse_sections(content_string):
    """Parses the content sections using mapped keys."""
    sections = {}
    # Split the content into sections based on "## Heading"
    parts = re.split(SECTION_SEPARATOR_PATTERN, content_string)

    if not parts:
        return sections

    # Handle the first section ("Descripción del Candidato") manually using mapping
    first_section_original_heading = METADATA_SEPARATOR.lstrip('#').strip()
    first_section_key = get_mapped_key(first_section_original_heading)
    first_section_content = clean_text(parts[0])
    if first_section_content:
        sections[first_section_key] = first_section_content

    # Process the remaining parts
    for part in parts[1:]:
        part = clean_text(part)
        if not part:
            continue

        try:
            heading, content = part.split('\n', 1)
            original_heading = clean_text(heading)
            json_key = get_mapped_key(original_heading)
            content = clean_text(content)

            # Specific handling for list-like sections based on ORIGINAL heading
            if original_heading in ["Redes Sociales", "Poder que postula", "Cursos"]:
                list_items = []
                split_lines = content.split('\n')
                for item in split_lines:
                    cleaned_item = clean_text(item.lstrip('- ')) # Handles '-' prefix
                    # Handle potential leading ',' for 'Cursos'
                    if original_heading == "Cursos":
                        cleaned_item = clean_text(cleaned_item.lstrip(', '))
                    if cleaned_item:
                        list_items.append(cleaned_item)
                sections[json_key] = list_items
            # Handle "Propuestas" as a list of paragraphs separated by '- '
            elif original_heading == "Propuestas":
                # Split by '\n- ' , clean up, and filter empty strings
                proposals = [clean_text(p) for p in re.split(r'\n-\s*', content) if clean_text(p)]
                # Remove the initial '-' if it exists on the first item after splitting
                if proposals and proposals[0].startswith('- '):
                     proposals[0] = clean_text(proposals[0][2:])
                sections[json_key] = proposals
            else:
                sections[json_key] = content # Store raw content for other sections

        except ValueError:
            original_heading = clean_text(part)
            if original_heading:
                json_key = get_mapped_key(original_heading)
                sections[json_key] = "" # Assign empty string if no content
            # print(f"Warning: Section part format unexpected: {part[:50]}...")

    return sections


# --- Main Execution ---

def process_files():
    """Processes all markdown files in the source folder."""
    print(f"Source folder: {os.path.abspath(SOURCE_FOLDER)}")
    print(f"Destination folder: {os.path.abspath(DESTINATION_FOLDER)}")

    if not os.path.isdir(SOURCE_FOLDER):
        print(f"Error: Source folder '{SOURCE_FOLDER}' not found.")
        return

    os.makedirs(DESTINATION_FOLDER, exist_ok=True)
    print(f"Ensured destination folder '{DESTINATION_FOLDER}' exists.")

    processed_count = 0
    error_count = 0

    for filename in os.listdir(SOURCE_FOLDER):
        if filename.lower().endswith(".md"):
            source_filepath = os.path.join(SOURCE_FOLDER, filename)
            base_name = os.path.splitext(filename)[0]
            dest_filepath = os.path.join(DESTINATION_FOLDER, f"{base_name}.json")

            print(f"Processing '{filename}'...")

            try:
                with open(source_filepath, 'r', encoding='utf-8') as f_in:
                    full_content = f_in.read()

                # Split content into metadata and main sections
                if METADATA_SEPARATOR in full_content:
                    metadata_part, sections_part = full_content.split(METADATA_SEPARATOR, 1)
                else:
                    print(f"  Warning: Metadata separator '{METADATA_SEPARATOR}' not found in '{filename}'. Skipping section parsing.")
                    metadata_part = full_content
                    sections_part = ""

                # Parse metadata first
                metadata_lines = metadata_part.strip().split('\n')
                metadata_dict = parse_metadata(metadata_lines) # Uses mapping

                # Parse sections
                sections_dict = {}
                if sections_part:
                    # Prepend the implicit first section heading before parsing
                    sections_content_to_parse = METADATA_SEPARATOR.lstrip('#').strip() + '\n' + sections_part.strip()
                    sections_dict = parse_sections(sections_content_to_parse) # Uses mapping

                # --- Structure the final JSON ---
                final_data = {}
                # Add section data first
                final_data.update(sections_dict)
                # Add the METADATA block at the end
                final_data["metadata"] = metadata_dict


                # Write the JSON file
                with open(dest_filepath, 'w', encoding='utf-8') as f_out:
                    json.dump(final_data, f_out, ensure_ascii=False, indent=4)

                print(f"  Successfully converted to '{dest_filepath}'")
                processed_count += 1

            except Exception as e:
                print(f"  Error processing file '{filename}': {e}")
                import traceback
                traceback.print_exc() # Print detailed traceback for debugging errors
                error_count += 1

    print("\n--- Processing Summary ---")
    print(f"Total files processed: {processed_count}")
    print(f"Total errors: {error_count}")

# --- Run the script ---
if __name__ == "__main__":
    process_files()