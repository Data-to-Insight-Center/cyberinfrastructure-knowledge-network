from .database import GraphDB
import json
from typing import Dict, Optional, Any


class MCReconstructor:
    """
    Re-constructs the model card from the Knowledge Graph
    """

    def __init__(self, uri, user, password):
        self.uri = uri
        self.user = user
        self.password = password

        try:
            self.db = GraphDB(self.uri, self.user, self.password)
            print("Connected to the Neo4j database.")
        except Exception as e:
            print("Error connecting to the Neo4j database:", str(e))

    def reconstruct(self, model_card_id):
        # Treat the provided id as a Model id and return the Model node
        metadata = {
            "model_id": str(model_card_id)
        }

        model_query = '''
            MATCH (m:Model {model_id: $model_id})
            RETURN m
            '''
        base_model = self.get_result_dict(model_query, "m", metadata)

        if base_model is None:
            return None

        return base_model

    def get_result_dict(self, query, type, metadata):
        response = self.db.get_result_query(query, metadata)
        if response is None:
            return None

        node = response[type]

        result_dict = {}
        if node is not None:
            for key in node.keys():
                result_dict[key] = node[key]
        else:
            return None
        return result_dict

    def search_kg(self, query):
        return []

    def get_all_mcs(self):
        """
        "Get all the model cards as a list"
        """
        models = self.db.get_all_modelcards()
        json_models = [
            {
                "model_id": record["model_id"],
                "name": record["name"],
                "version": record.get("version"),
                "description": record.get("description")
            }
            for record in models
        ]
        return json_models

    def get_model_location(self, model_id):
        """
        Get the model location as the download URL
        """
        model_info = self.db.get_model_location(model_id)

        if model_info is None:
            return None
        else:
            json_model = {
                "model_id": model_info["model_id"],
                "name": model_info["name"],
                "version": model_info["version"],
                "download_url": model_info["download_url"]
            }
            return json_model

    def get_deployments(self, model_id):
        """
        Get the deployments for a given model_id
        """
        deployment_info = self.db.get_deployments(model_id)
        if deployment_info is None:
            return None
        return deployment_info

    def get_deployment_ids(self, model_id):
        """
        Get only the deployment IDs for a given model_id
        """
        return self.db.get_deployment_ids(model_id)

    def set_model_location(self, model_id, location):
        """
        Update the model location
        """
        self.db.set_model_location(model_id, location)


    def get_link_headers(self, model_card) -> Dict[str, str]:
        """
        Generates HTTP Link and Content-Length headers based on model card data,
        targeting specific fields like author, input_data, model location, etc.

        Args:
            model_card_id: id of the model card
        Returns:
            A dictionary containing 'Link' and 'Content-Length' headers.
            The 'Link' header will contain relations based on available data.
            The 'Content-Length' will be '0'.
        """
        links = []

        model_card_id: str = model_card.get('external_id')
        author: str = model_card.get('author')
        input_data_url: str = model_card.get('input_data')

        ai_model_dict: Dict[str, Any] = model_card.get('ai_model', {})

        model_location_url: Optional[str] = ai_model_dict.get('location')
        inference_labels_url: Optional[str] = ai_model_dict.get('inference_labels')

        # Assembling links
        links.append(f'<{model_card_id}>; rel="cite-as"')

        if author and isinstance(author, str) and author.startswith(('http://', 'https://')):
            links.append(f'<{author}>; rel="author"')
        else:
            links.append(f'<http://tapis.com/{author}>; rel="author"')

        if input_data_url and isinstance(input_data_url, str) and input_data_url.startswith(('http://', 'https://')):
            links.append(f'<{input_data_url}>; rel="item"; title="input_data"')

        if model_location_url and isinstance(model_location_url, str) and model_location_url.startswith(
                ('http://', 'https://')):
            links.append(f'<{model_location_url}>; rel="item"; title="model_location"')

        if inference_labels_url and isinstance(inference_labels_url, str) and inference_labels_url.startswith(
                ('http://', 'https://')):
            links.append(f'<{inference_labels_url}>; rel="item"; title="inference_labels"')

        # Assembling the header
        headers = {}
        link_header_value = ", ".join(links)

        if link_header_value:
            headers['Link'] = link_header_value

        # Setting the Content-Length for an empty body response
        headers['Content-Length'] = '0'

        return headers
    
    def get_average_compute_time(self, mc_id):
        """
        For a given model id, compute average of d.avg_compute_time over its deployments.
        """
        return self.db.get_average_compute_time(mc_id)


    def get_all_model_ids(self):
        """
        Get all model card IDs from the database.
        Returns a list of model card IDs.
        """
        return self.db.get_all_model_ids()

    def get_average_statistic_for_model(self, model_id, statistic):
        """
        Get the average of a specific statistic across all deployments for a given model.
        Returns a dictionary with the model ID, statistic name, average value, and deployment count.
        """
        return self.db.get_average_statistic_for_model(model_id, statistic)

    def get_average_compute_time_all_models(self):
        """
        Get list of all models with their average compute time across deployments.
        """
        return self.db.get_average_compute_time_all_models()

    def get_average_cpu_gpu_all_models(self):
        """
        Get list of all models with average CPU and GPU power across deployments.
        """
        return self.db.get_average_cpu_gpu_all_models()

    def get_average_accuracy_all_models(self):
        """
        Get list of all models with average accuracy across deployments.
        """
        return self.db.get_average_accuracy_all_models()
