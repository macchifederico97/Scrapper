from pathlib import Path
import json
from legacy.WebService.WSPipelineFile import setFileMappingPy


def getID_pipelines(bifrost_instance: str):
    """
    Scrapes the last pipeline execution filtered by name.
    Returns a dictionary with start time, finish time, and duration in minutes.
    """

    outputList = [] #Output list containing pipeline information dict

    #TODO - festione con parametro, se true aggiorna il file, se false controlla timestamp ultimo aggiornamento e se >24h aggiorna, altrimenti legge il file
    setFileMappingPy(bifrost_instance, True)

    
    with open(f"client/{bifrost_instance}/pipeline.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print("Ultimo aggiornamento:", data["last_updated"])
    for pipeline in data["pipelines"]:
        pipeDict = {"pipeline_name": pipeline['pipeline_name'], "pipeline_id": pipeline['pipeline_id']}
        outputList.append(pipeDict) 


    return outputList