import csv
import json
import os
import sys

def csv_to_json_per_candidate(csv_file_path):
    """
    Reads each row from the CSV file and creates a separate JSON file
    for each candidate in a folder named 'data'. Fields that are "no reportó"
    will be replaced with "No reportó <nombre_del_campo>" in the description.
    """
    # Ensure the output folder exists
    os.makedirs("data", exist_ok=True)
    
    # Helper function to handle "no reportó" logic
    def field_or_no_report(field_value):
        """
        If 'field_value' is "no reportó" (case-insensitive),
        """
        if field_value.strip().lower() == "no proporcionó":
            return False
        return True

    with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        for row in csv_reader:
            # Apply "no reportó" logic to the requested fields
            escolaridad_val = f"tiene grado de escolaridad \"{row['ESCOLARIDAD']}\" " if field_or_no_report(row['ESCOLARIDAD']) else "No reportó escolaridad "
            estatus_esc_val = f"con status {row['ESTATUS_ESCOLARIDAD']}." if field_or_no_report(row['ESTATUS_ESCOLARIDAD']) else "sin estatus de escolaridad."
            #telefono_val = f"Reportó el telefono {row['TELEFONO']}" if field_or_no_report(row['TELEFONO'],) else "No reportó teléfono"
            #correo_val = f"y el correo electronico {row['CORREO_ELECTRONICO']}" if field_or_no_report(row['CORREO_ELECTRONICO']) else "No reportó correo electrónico"
            pagina_web_val =f"Reporta la página web {row['PAGINA_WEB']}" if field_or_no_report(row['PAGINA_WEB']) else "No reportó página web"
            redes_val =f"y reporta las siguientes redes sociales \"{row['REDES']}\". " if field_or_no_report(row['REDES'])  else "y no reportó redes sociales. "    
            cursos_val =f" Ha tomado los siguientes cursos \"{row['CURSOS']}\"" if field_or_no_report(row['CURSOS']) else "No reportó cursos" 
            trayectoria_val = f"y tiene la siguiente trayectoria academica \"{row['TRAYECTORIA_ACADEMICA']}\"" if field_or_no_report(row['TRAYECTORIA_ACADEMICA']) else " y no reportó trayectoria académica."            
            motivo_val = f"Su motivo para el cargo publico es \"{row['MOTIVO_CARGO_PUBLICO']}\"." if field_or_no_report(row['MOTIVO_CARGO_PUBLICO']) else "No reportó motivo para el cargo público."
            vision_j_val =f"Su vision para la funcion jurisdiccional es \"{row['VISION_FUNCION_JURISDICCIONAL']}\". " if field_or_no_report(row['VISION_FUNCION_JURISDICCIONAL']) else "No reportó visión para la función jurisdiccional. "
            vision_i_val =f"Su vision para la imparticion de justicia es \"{row['VISION_IMPARTICION_JUSTICIA']}\". " if field_or_no_report(row['VISION_IMPARTICION_JUSTICIA']) else "No reportó visión para la impartición de justicia. "
            prop1_val = f"\"{row['PROPUESTA_1']}\"" if field_or_no_report(row['PROPUESTA_1']) else "No reportó propuesta 1."
            prop2_val = f"\"{row['PROPUESTA_2']}\"" if field_or_no_report(row['PROPUESTA_2']) else "No reportó propuesta 2."
            prop3_val = f"\"{row['PROPUESTA_3']}\"" if field_or_no_report(row['PROPUESTA_3']) else "No reportó propuesta 3."

            # Build the description text with the updated fields
            description = (
                f"El candidato {row['NOMBRE_CANDIDATO']} "
                f"{escolaridad_val}"
                f"{estatus_esc_val}" 
                f"Se postula para el puesto {row['CARGO']} "
                f"por la entidad {row['ENTIDAD']} y es postulado por {row['PODER_POSTULA']}."
                f"{pagina_web_val} {redes_val}."
                f"{cursos_val} {trayectoria_val}."
                f"Su currículum se encuentra en {row['CURRICULUM_VITAE']}."
                f"{motivo_val}"
                f"{vision_j_val}"
                f"{vision_i_val}"
                f"Cuenta con las siguientes propuestas:\n"
                f"- {prop1_val}\n"
                f"- {prop2_val}\n"
                f"- {prop3_val}."
            )
            
            # Build the Metadata dictionary (using the raw CSV fields here,
            # assuming you still want their original values in Metadata)
            metadata = {
                "Nombre": row["NOMBRE_CANDIDATO"],
                "Cargo": row["CARGO"],
                "Entidad": row["ENTIDAD"],
                "Numero de lista en boleta": row["NUM_LISTA_EN_BOLETA"],
                "Poder postulado": row["PODER_POSTULA"],
                "Sexo": row["SEXO"],
                "Telefono": row["TELEFONO"],
                "Correo Electronico": row["CORREO_ELECTRONICO"],
                "Escolaridad": row["ESCOLARIDAD"],
                "Estatus de escolaridad": row["ESTATUS_ESCOLARIDAD"]
            }
            
            # Combine into one dictionary for the JSON
            output_data = {
                "Description": description,
                "Metadata": metadata
            }
            
            # Create a file name using the candidate's name (replacing spaces with underscores)
            candidate_name = row["NOMBRE_CANDIDATO"].replace(" ", "_")
            output_file_path = os.path.join("data", f"{candidate_name}.json")
            
            # Write the JSON file
            with open(output_file_path, mode='w', encoding='utf-8') as json_file:
                json.dump(output_data, json_file,ensure_ascii=False, indent=4)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <input_csv>")
        sys.exit(1)

    csv_file_path = sys.argv[1]
    csv_to_json_per_candidate(csv_file_path)
