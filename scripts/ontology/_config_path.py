import os
from typing import Optional

DEFAULT_ONTOLOGY_METADATA_CONFIG_FILENAME = "ontology_metadata_config.json"


def get_ontology_config_file(ontology_metadata_config_file: Optional[str]) -> str:
    if not ontology_metadata_config_file:
        ontology_metadata_config_file = os.path.join(os.getcwd(), DEFAULT_ONTOLOGY_METADATA_CONFIG_FILENAME)
    return ontology_metadata_config_file
