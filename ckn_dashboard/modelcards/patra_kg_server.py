import requests


def search_kg(query, api_uri):
    """
    Perform a search using a REST API GET endpoint and parse the response to extract IDs.
    """
    search_uri = api_uri + "/search"
    params = {'q': query}
    response = requests.get(search_uri, params=params)
    response.raise_for_status()

    # parse the data
    data = response.json()
    if data is None:
        return []
    else:
        ids = [item['mc_id'] for item in data]
    return ids


def retrieve_mc(mc_id, api_uri):
    """
    Perform a search using a REST API GET endpoint and parse the response to extract IDs.
    """
    retrieve_uri = api_uri + "/download_mc"
    params = {'id': mc_id}
    response = requests.get(retrieve_uri, params=params)
    response.raise_for_status()

    # parse the data
    data = response.json()
    if data is None:
        return {}
    else:
        return data
