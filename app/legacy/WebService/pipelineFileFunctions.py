import json
import sys
#from datetime import datetime

def getData(file_path: str):    #TODO LEGGERE DIRETTAMENTE IL FILE DA CLIENT, SENZA RICHIEDERE PATH, SOLTANTO CON BIFROST_INSTANCE
    """Legge e restituisce i dati del file JSON, oppure una struttura vuota se non esiste."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_updated": None, "pipelines": []}

def smartAppendData(file_path: str, new_data: dict):
    sys.path.insert(0, "legacy/WebService")
    """
    Aggiorna o aggiunge pipeline nel file JSON esistente,
    aggiornando anche il campo 'last_updated' con quello del nuovo file.

    :param file_path: percorso del file JSON
    :param new_data: dizionario strutturato come il file di output,
                     es: {"last_updated": "...", "pipelines": [ {...}, {...} ]}
    """
    # 1. Legge il file esistente
    data = getData(file_path)

    # 2. Aggiorna il campo last_updated se presente nel nuovo file
    if new_data.get("last_updated"):
        data["last_updated"] = new_data["last_updated"]

    # 3. Prepara la lista delle pipeline
    existing_pipelines = data.get("pipelines", [])
    new_pipelines = new_data.get("pipelines", [])

    # 4. Aggiorna o aggiunge pipeline
    for new_pipeline in new_pipelines:
        found = False
        for existing_pipeline in existing_pipelines:
            if existing_pipeline.get("pipeline_id") == new_pipeline.get("pipeline_id"):
                existing_pipeline.update(new_pipeline)
                found = True
                break
        if not found:
            existing_pipelines.append(new_pipeline)
            print(f"Aggiunta nuova pipeline: {new_pipeline.get('pipeline_name', new_pipeline.get('pipeline_id'))}")

    # 5. Aggiorna il campo pipelines nel file principale
    data["pipelines"] = existing_pipelines

    # 6. Salva tutto

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    sys.path.pop(0)

    print(f"Dati aggiornati. Ultimo aggiornamento: {data['last_updated']}")
