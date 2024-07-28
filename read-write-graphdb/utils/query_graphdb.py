import requests
import urllib.parse
import json
import pandas as pd
import rdflib
from rdflib import Graph, URIRef, XSD, Literal
from rdflib.namespace import RDF, RDFS
import math
import os
from utils import save_workflow

base_url = "http://localhost:8080"
repository = "test-repo"
last_inserted_user= None

def execute_sparql_query(base_url, repository, query):
    """
    Executes a SPARQL query using GraphDB's REST API and returns the results.
    
    Args:
    - base_url (str): The base URL of the GraphDB server.
    - repository (str): The name of the GraphDB repository.
    - query (str): The SPARQL query to execute.
    
    Returns:
    - dict: The JSON response from the SPARQL endpoint.
    """
    try:
        # URL encode the query using quote_plus for proper URL encoding
        encoded_query = urllib.parse.quote_plus(query)
        
        url = f"{base_url}/repositories/{repository}?query={encoded_query}"
        
        headers = {
            "Accept": "application/sparql-results+json"
        }
        
        # Make the GET request to the SPARQL endpoint
        response = requests.get(url, headers=headers)
        
        response.raise_for_status()  

        return response.json()
        
    except requests.exceptions.RequestException as e:
        # Log the exception details and re-raise it
        print(f"Failed to execute SPARQL query. Error: {str(e)}")
        raise

def get_intent(user, dataset):
    """
    Retrieves the most used intent associated with a user and dataset.
    
    Args:
    - user (str): The user identifier.
    - dataset (str): The dataset identifier.
    
    Returns:
    - str: The most used intent.
    """
    
    found = False
    intent = None
    
    # Check if the user has used the dataset before
    query = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX ml: <http://localhost/8080/intentOntology#>

    SELECT ?intent (COUNT(?intent) AS ?count)
    WHERE {{
        ml:{user} ml:runs ?workflow.
        ?workflow ml:hasInput ml:{dataset}.
        ?workflow ml:achieves ?task.
        ?task ml:hasIntent ?intent 
    }}
    GROUP BY ?intent
    ORDER BY DESC(?count)
    LIMIT 1
    """
    
    results = execute_sparql_query(base_url, repository, query)
    
    if results["results"]["bindings"]:
        intent = results["results"]["bindings"][0]["intent"]["value"]
        found = True
    
    # If not found, look for the dataset usage by any user
    if not found:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT ?intent (COUNT(?intent) AS ?count)
        WHERE {{
            ?workflow ml:hasInput ml:{dataset}.
            ?workflow ml:achieves ?task.
            ?task ml:hasIntent ?intent 
        }}
        GROUP BY ?intent
        ORDER BY DESC(?count)
        LIMIT 1
        """
        
        results = execute_sparql_query(base_url, repository, query)
        
        if results["results"]["bindings"]:
            intent = results["results"]["bindings"][0]["intent"]["value"]
            found = True
    
    # If still not found, look for the most used intent by the user
    if not found:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT ?intent (COUNT(?intent) AS ?count)
        WHERE {{
            ml:{user} ml:runs ?workflow.
            ?workflow ml:achieves ?task.
            ?task ml:hasIntent ?intent 
        }}
        GROUP BY ?intent
        ORDER BY DESC(?count)
        LIMIT 1
        """
        
        results = execute_sparql_query(base_url, repository, query)
        
        if results["results"]["bindings"]:
            intent = results["results"]["bindings"][0]["intent"]["value"]
            found = True
    
    # If still not found, get the most used intent overall
    if not found:
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT ?intent (COUNT(?intent) AS ?count)
        WHERE {
            ?task ml:hasIntent ?intent 
        }
        GROUP BY ?intent
        ORDER BY DESC(?count)
        LIMIT 1
        """
        
        results = execute_sparql_query(base_url, repository, query)
        
        if results["results"]["bindings"]:
            intent = results["results"]["bindings"][0]["intent"]["value"]
            found = True
    
    return intent.split("#")[-1]

def get_metric(user, dataset, intent):
    """
    Retrieves the most used metric associated with a user, dataset, and intent.
    
    Args:
    - user (str): The user identifier.
    - dataset (str): The dataset identifier.
    - intent (str): The intent identifier.
    
    Returns:
    - str: The most used metric.
    """
    
    found = False
    metric = None
    
    # Check if the user has used the dataset for the intent
    query = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX ml: <http://localhost/8080/intentOntology#>

    SELECT ?metric (COUNT(?metric) AS ?count)
    WHERE {{
        ml:{user} ml:runs ?workflow.
        ?workflow ml:hasInput ml:{dataset}.
        ?workflow ml:achieves ?task.
        ?task ml:hasIntent ml:{intent}.
        ?task ml:hasRequirement ?eval.
        ?eval ml:onMetric ?metric 
    }}
    GROUP BY ?metric
    ORDER BY DESC(?count)
    LIMIT 1
    """
    
    results = execute_sparql_query(base_url, repository, query)
    
    if results["results"]["bindings"]:
        metric = results["results"]["bindings"][0]["metric"]["value"]
        found = True
    
    # If not found, look for the dataset usage by any user for the intent
    if not found:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT ?metric (COUNT(?metric) AS ?count)
        WHERE {{
            ?workflow ml:hasInput ml:{dataset}.
            ?workflow ml:achieves ?task.
            ?task ml:hasIntent ml:{intent}.
            ?task ml:hasRequirement ?eval.
            ?eval ml:onMetric ?metric 
        }}
        GROUP BY ?metric
        ORDER BY DESC(?count)
        LIMIT 1
        """
        
        results = execute_sparql_query(base_url, repository, query)
        
        if results["results"]["bindings"]:
            metric = results["results"]["bindings"][0]["metric"]["value"]
            found = True
    
    # If still not found, look for the most used metric by the user for the intent
    if not found:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT ?metric (COUNT(?metric) AS ?count)
        WHERE {{
            ml:{user} ml:runs ?workflow.
            ?workflow ml:achieves ?task.
            ?task ml:hasIntent ml:{intent}.
            ?task ml:hasRequirement ?eval.
            ?eval ml:onMetric ?metric 
        }}
        GROUP BY ?metric
        ORDER BY DESC(?count)
        LIMIT 1
        """
        
        results = execute_sparql_query(base_url, repository, query)
        
        if results["results"]["bindings"]:
            metric = results["results"]["bindings"][0]["metric"]["value"]
            found = True
    
    # If still not found, get the most used metric overall for the intent
    if not found:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT ?metric (COUNT(?metric) AS ?count)
        WHERE {{
            ?task ml:hasIntent ml:{intent}.
            ?task ml:hasRequirement ?eval.
            ?eval ml:onMetric ?metric 
        }}
        GROUP BY ?metric
        ORDER BY DESC(?count)
        LIMIT 1
        """
        
        results = execute_sparql_query(base_url, repository, query)
        
        if results["results"]["bindings"]:
            metric = results["results"]["bindings"][0]["metric"]["value"]
            found = True
    
    return metric.split("#")[-1]


def get_preprocessing(user, dataset, intent):
    found = False
    preprocessing = True

    # Check if the user has used the dataset for the intent with ConstraintNoPreprocessing
    query = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX ml: <http://localhost/8080/intentOntology#>

    SELECT (COUNT(DISTINCT ?task) AS ?constraintTaskCount)
    WHERE {{
        ml:{user} ml:runs ?workflow.
        ?workflow ml:hasInput ml:{dataset}.
        ?workflow ml:achieves ?task.
        ?task ml:hasIntent ml:{intent}.
        ?task ml:hasConstraint ml:ConstraintNoPreprocessing
    }}
    """
    results = execute_sparql_query(base_url, repository, query)

    if results["results"]["bindings"]:
        constraint_task = int(results["results"]["bindings"][0]["constraintTaskCount"]["value"])
        found = True

    if found:
        # Count total tasks achieved by the user with the dataset
        query_aux = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT (COUNT(DISTINCT ?task) AS ?taskCount)
        WHERE {{
            ml:{user} ml:runs ?workflow.
            ?workflow ml:hasInput ml:{dataset}.
            ?workflow ml:achieves ?task.
        }}
        """
        results_aux = execute_sparql_query(base_url, repository, query_aux)

        if results_aux["results"]["bindings"]:
            total_tasks = int(results_aux["results"]["bindings"][0]["taskCount"]["value"])

            if total_tasks > 0:
                if constraint_task / total_tasks < 0.5:
                    preprocessing = True
                else:
                    preprocessing = False

    if not found:
        # Count total tasks achieved by any user with the dataset
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT (COUNT(DISTINCT ?task) AS ?constraintTaskCount)
        WHERE {{
            ?workflow ml:hasInput ml:{dataset}.
            ?workflow ml:achieves ?task.
            ?task ml:hasConstraint ml:ConstraintNoPreprocessing
        }}
        """
        results = execute_sparql_query(base_url, repository, query)

        if results["results"]["bindings"]:
            constraint_task = int(results["results"]["bindings"][0]["constraintTaskCount"]["value"])
            found = True

        if found:
            query_aux = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ml: <http://localhost/8080/intentOntology#>

            SELECT (COUNT(DISTINCT ?task) AS ?taskCount)
            WHERE {{
                ?workflow ml:hasInput ml:{dataset}.
                ?workflow ml:achieves ?task.
            }}
            """
            results_aux = execute_sparql_query(base_url, repository, query_aux)

            if results_aux["results"]["bindings"]:
                total_tasks = int(results_aux["results"]["bindings"][0]["taskCount"]["value"])

                # Check if total_tasks is not zero to avoid division by zero
                if total_tasks > 0:
                    if constraint_task / total_tasks < 0.5:
                        preprocessing = True
                    else:
                        preprocessing = False

    if not found:
        # Count tasks achieved by the user with the intent and ConstraintNoPreprocessing
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT (COUNT(DISTINCT ?task) AS ?constraintTaskCount)
        WHERE {{
            ml:{user} ml:runs ?workflow.
            ?workflow ml:achieves ?task.
            ?task ml:hasIntent ml:{intent}.
            ?task ml:hasConstraint ml:ConstraintNoPreprocessing
        }}
        """
        results = execute_sparql_query(base_url, repository, query)

        if results["results"]["bindings"]:
            constraint_task = int(results["results"]["bindings"][0]["constraintTaskCount"]["value"])
            found = True

        if found:
            query_aux = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ml: <http://localhost/8080/intentOntology#>

            SELECT (COUNT(DISTINCT ?task) AS ?taskCount)
            WHERE {{
                ml:{user} ml:runs ?workflow.
                ?workflow ml:achieves ?task.
                ?task ml:hasIntent ml:{intent}
            }}
            """
            results_aux = execute_sparql_query(base_url, repository, query_aux)

            if results_aux["results"]["bindings"]:
                total_tasks = int(results_aux["results"]["bindings"][0]["taskCount"]["value"])

                # Check if total_tasks is not zero to avoid division by zero
                if total_tasks > 0:
                    if constraint_task / total_tasks < 0.5:
                        preprocessing = True
                    else:
                        preprocessing = False

    if not found:
        # Count tasks achieved by any user with the intent and ConstraintNoPreprocessing
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT (COUNT(DISTINCT ?task) AS ?constraintTaskCount)
        WHERE {{
            ?task ml:hasIntent ml:{intent}.
            ?task ml:hasConstraint ml:ConstraintNoPreprocessing
        }}
        """
        results = execute_sparql_query(base_url, repository, query)

        if results["results"]["bindings"]:
            constraint_task = int(results["results"]["bindings"][0]["constraintTaskCount"]["value"])
            found = True

        if found:
            query_aux = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ml: <http://localhost/8080/intentOntology#>

            SELECT (COUNT(DISTINCT ?task) AS ?taskCount)
            WHERE {{
                ?task ml:hasIntent ml:{intent}
            }}
            """
            results_aux = execute_sparql_query(base_url, repository, query_aux)

            if results_aux["results"]["bindings"]:
                total_tasks = int(results_aux["results"]["bindings"][0]["taskCount"]["value"])

                # Check if total_tasks is not zero to avoid division by zero
                if total_tasks > 0:
                    if constraint_task / total_tasks < 0.5:
                        preprocessing = True
                    else:
                        preprocessing = False

    return preprocessing


def get_algorithm(user, dataset, intent):
    found = False
    algorithm = None
    
    # Check if the user has used the dataset with a specific algorithm constraint
    query = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX ml: <http://localhost/8080/intentOntology#>

    SELECT ?algorithm (COUNT(?algorithm) AS ?count)
    WHERE {{
        ml:{user} ml:runs ?workflow.
        ?workflow ml:hasInput ml:{dataset}.
        ?workflow ml:achieves ?task.
        ?task ml:hasConstraint ?constraint.
        ?constraint rdf:type ml:ConstraintAlgorithm.
        ?constraint ml:on ?algorithm 
    }}
    GROUP BY ?algorithm
    ORDER BY DESC(?count)
    LIMIT 1
    """
    
    results = execute_sparql_query(base_url, repository, query)
    
    if results["results"]["bindings"]:
        algorithm = results["results"]["bindings"][0]["algorithm"]["value"]
        found = True
    
    # If not found, look for other users' usage of the dataset
    if not found:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT ?algorithm (COUNT(?algorithm) AS ?count)
        WHERE {{
            ?workflow ml:hasInput ml:{dataset}.
            ?workflow ml:achieves ?task.
            ?task ml:hasConstraint ?constraint.
            ?constraint rdf:type ml:ConstraintAlgorithm.
            ?constraint ml:on ?algorithm 
        }}
        GROUP BY ?algorithm
        ORDER BY DESC(?count)
        LIMIT 1
        """
        
        results = execute_sparql_query(base_url, repository, query)
        
        if results["results"]["bindings"]:
            algorithm = results["results"]["bindings"][0]["algorithm"]["value"]
            found = True
    
    # If still not found, look for the user's usage of the same intent
    if not found:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT ?algorithm (COUNT(?algorithm) AS ?count)
        WHERE {{
            ml:{user} ml:runs ?workflow.
            ?workflow ml:achieves ?task.
            ?task ml:hasIntent ml:{intent}.
            ?task ml:hasConstraint ?constraint.
            ?constraint rdf:type ml:ConstraintAlgorithm.
            ?constraint ml:on ?algorithm 
        }}
        GROUP BY ?algorithm
        ORDER BY DESC(?count)
        LIMIT 1
        """
        
        results = execute_sparql_query(base_url, repository, query)
        
        if results["results"]["bindings"]:
            algorithm = results["results"]["bindings"][0]["algorithm"]["value"]
            found = True
    
    # If still not found, get the most used algorithm for the intent overall
    if not found:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT ?algorithm (COUNT(?algorithm) AS ?count)
        WHERE {{
            ?task ml:hasIntent ml:{intent}.
            ?task ml:hasConstraint ?constraint.
            ?constraint rdf:type ml:ConstraintAlgorithm.
            ?constraint ml:on ?algorithm 
        }}
        GROUP BY ?algorithm
        ORDER BY DESC(?count)
        LIMIT 1
        """
        
        results = execute_sparql_query(base_url, repository, query)
        
        if results["results"]["bindings"]:
            algorithm = results["results"]["bindings"][0]["algorithm"]["value"]
            found = True
    
    return algorithm.split("#")[-1] if algorithm else None


def get_preprocessing_algorithm(user, dataset, intent):
    """
    Retrieves the most used preprocessing algorithm associated with a user, dataset, and intent.
    
    Args:
    - user (str): The user identifier.
    - dataset (str): The dataset identifier.
    - intent (str): The intent identifier.
    
    Returns:
    - str: The most used preprocessing algorithm.
    """
    
    found = False
    algorithm = None
    
    # Check if the user has used the dataset with a preprocessing algorithm
    query = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX ml: <http://localhost/8080/intentOntology#>

    SELECT ?algorithm (COUNT(?algorithm) AS ?count)
    WHERE {{
        ml:{user} ml:runs ?workflow.
        ?workflow ml:hasInput ml:{dataset}.
        ?workflow ml:achieves ?task.
        ?task ml:hasConstraint ?constraint.
        ?constraint rdf:type ml:ConstraintPreprocessingAlgorithm.
        ?constraint ml:on ?algorithm 
    }}
    GROUP BY ?algorithm
    ORDER BY DESC(?count)
    LIMIT 1
    """
    
    results = execute_sparql_query(base_url, repository, query)
    
    if results["results"]["bindings"]:
        algorithm = results["results"]["bindings"][0]["algorithm"]["value"]
        found = True
    
    # If not found, look for the dataset usage by any user with a preprocessing algorithm
    if not found:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT ?algorithm (COUNT(?algorithm) AS ?count)
        WHERE {{
            ?workflow ml:hasInput ml:{dataset}.
            ?workflow ml:achieves ?task.
            ?task ml:hasConstraint ?constraint.
            ?constraint rdf:type ml:ConstraintPreprocessingAlgorithm.
            ?constraint ml:on ?algorithm 
        }}
        GROUP BY ?algorithm
        ORDER BY DESC(?count)
        LIMIT 1
        """
        
        results = execute_sparql_query(base_url, repository, query)
        
        if results["results"]["bindings"]:
            algorithm = results["results"]["bindings"][0]["algorithm"]["value"]
            found = True
    
    # If still not found, look for the user's usages of the same intent with a preprocessing algorithm
    if not found:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT ?algorithm (COUNT(?algorithm) AS ?count)
        WHERE {{
            ml:{user} ml:runs ?workflow.
            ?workflow ml:achieves ?task.
            ?task ml:hasIntent ml:{intent}.
            ?task ml:hasConstraint ?constraint.
            ?constraint rdf:type ml:ConstraintPreprocessingAlgorithm.
            ?constraint ml:on ?algorithm 
        }}
        GROUP BY ?algorithm
        ORDER BY DESC(?count)
        LIMIT 1
        """
        
        results = execute_sparql_query(base_url, repository, query)
        
        if results["results"]["bindings"]:
            algorithm = results["results"]["bindings"][0]["algorithm"]["value"]
            found = True
    
    # If still not found, get the most used preprocessing algorithm overall for the intent
    if not found:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ml: <http://localhost/8080/intentOntology#>

        SELECT ?algorithm (COUNT(?algorithm) AS ?count)
        WHERE {{
            ?task ml:hasIntent ml:{intent}.
            ?task ml:hasConstraint ?constraint.
            ?constraint rdf:type ml:ConstraintPreprocessingAlgorithm.
            ?constraint ml:on ?algorithm 
        }}
        GROUP BY ?algorithm
        ORDER BY DESC(?count)
        LIMIT 1
        """
        
        results = execute_sparql_query(base_url, repository, query)
        
        if results["results"]["bindings"]:
            algorithm = results["results"]["bindings"][0]["algorithm"]["value"]
            found = True
    
    return algorithm.split("#")[-1]


def get_users_with_workflows():
    
    query = """
    PREFIX ml: <http://localhost/8080/intentOntology#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT DISTINCT ?user
    WHERE {
      ?user ml:runs ?workflow .
    }
    """
    results = execute_sparql_query(base_url, repository, query)
    users = []
    if results["results"]["bindings"]:
        users = [binding["user"]["value"].split('#')[-1] for binding in results["results"]["bindings"]]
    
    return users


def get_users():
    global last_inserted_user  # Declare the use of the global variable
    
    query = """
    PREFIX ml: <http://localhost/8080/intentOntology#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT DISTINCT ?user
    WHERE {
    ?user rdf:type ml:User .
    }
    """
    results = execute_sparql_query(base_url, repository, query)
    users = []
    if results["results"]["bindings"]:
        users = [binding["user"]["value"].split('#')[-1] for binding in results["results"]["bindings"]]


    # Extract numeric part and find the highest number
    user_numbers = []
    for user in users:
        if user.startswith("User"):
            num_part = user[4:] 
            user_numbers.append(int(num_part))
    
    next_user_number = max(user_numbers) if user_numbers else 0
    new_user = f"User{next_user_number}"

    last_inserted_user = new_user
    
    return {
        "users": users,
        "last_inserted_user": last_inserted_user
    }


def create_insert_user_query_template(repository_id):

    # TO BE USED FOR DATA UPDATE CASES

    url = f"http://localhost:8080/rest/repositories/{repository_id}/sparql-templates"
    
    template_id = "http://localhost/8080/intentOntology#insert_user_template"
    
    query = """
    PREFIX ml: <http://localhost/8080/intentOntology#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    INSERT DATA {
      ml:User0 rdf:type ml:User ;
                ml:name "username0" ;
                ml:email "user0@example.com" ;
                ml:password "pass0" .
    }
    """
    
    data = {
        "templateID": template_id,
        "query": query
    }
    
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code != 201:
        raise Exception(f"Error: Received status code {response.status_code}. Response: {response.text}")
    
    print(f"Created template: {template_id}")

    return


def get_query_template_configuration(template_id, repository_id):
    
    # TO BE USED FOR DATA UPDATE CASES

    url = f"http://localhost:8080/rest/repositories/{repository_id}/sparql-templates/configuration"
    
    params = {
        "templateID": template_id
    }

    headers = {
        'accept': 'text/plain'
    }

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        raise Exception(f"Error: Received status code {response.status_code}. Response: {response.text}")

    return response.text


def add_new_user(email):
    result = get_users()  # Call the updated get_users function
    last_inserted_user = result["last_inserted_user"]   
    repository_id = repository
    url = f"http://localhost:8080/repositories/{repository_id}/statements"

    headers = {
        "Content-Type": "application/sparql-update"
    }

    # print(last_inserted_user)
    numeric_part = ''.join(filter(str.isdigit, last_inserted_user))
    new_user_id = f"User{int(numeric_part) + 1}"

    query = f"""
    PREFIX ml: <http://localhost/8080/intentOntology#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    INSERT DATA {{
        ml:{new_user_id} rdf:type ml:User ;
                ml:email "{email}".    
    }}
    """

    response = requests.post(url, headers=headers, data=query)

    if response.status_code == 204:
        # Update the last inserted user
        last_inserted_user = new_user_id
        print(f"Added new user: {new_user_id}")
        return new_user_id

    else:
        print(f"Error {response.status_code}: {response.text}")
        return None


def find_user_by_email(email):
    # Create a SPARQL query
    query = f"""
    PREFIX ml: <http://localhost/8080/intentOntology#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT DISTINCT ?user
    WHERE {{
        ?user rdf:type ml:User .
        ?user ml:email "{email}" .
    }}
    """
    results = execute_sparql_query(base_url, repository, query)
    if results["results"]["bindings"]:
        return results["results"]["bindings"][0]["user"]["value"].split('#')[-1]  # Return the first user directly
    
    return None


def add_new_dataset(dataset_name):
    repository_id = repository
    url = f"http://localhost:8080/repositories/{repository_id}/statements"

    headers = {
        "Content-Type": "application/sparql-update"
    }

    dataset_uri = f"http://localhost/8080/intentOntology#{dataset_name}"

    query = f"""
    PREFIX ns_dmop: <http://www.e-lico.eu/ontologies/dmo/DMOP/DMOP.owl#>
    PREFIX RDF: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    INSERT DATA {{
        <{dataset_uri}> RDF:type ns_dmop:DataSet .
    }}
    """

    response = requests.post(url, headers=headers, data=query)

    # Check the response status code
    if response.status_code == 204:
        print(f"Added new dataset: {dataset_name}")
        return dataset_name
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None


def add_new_workflow(data):
    repository_id = repository
    url = f"http://localhost:8080/repositories/{repository_id}/statements"

    headers = {
        "Content-Type": "application/sparql-update"
    }

    insert_query, workflow_uri, user_uri, workflow_name = save_workflow.generate_sparql_insert_query(data)

    response = requests.post(url, headers=headers, data=insert_query)

    # Check the response status code
    if response.status_code == 204:
        print(f"Added new workflow: {workflow_uri} for the user {user_uri}")
        return workflow_name
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None


# if __name__ == "__main__":
    # users_with_workflows = get_users_with_workflows()
    # print(users_with_workflows)
    # users = get_users()
    # print("Available users in the system:")
    # print(users)
    # email = "userX@example.com"
    # inserted_user = add_new_user(email)
    # print(inserted_user)
    # users = get_users()
    # print("Available users in the system:")
    # print(users)
    # create_insert_user_query_template(repository)
#     user = find_user_by_email("userX@example.com")
#     print(user)
#     dataset_name = "datasetX"
#     result = add_new_dataset(dataset_name)

#     data = {
#     'user': 'john_doe',
#     'dataset': 'iris',
#     'intent': 'Classification',
#     'algorithm_constraint': 'SVC',
#     'hyperparam_constraints': {
        
#     },
#     'time': 100,
#     'preprocessor_constraint': 'StandardScaler',
#     'time': 100,
#     'max_time': 300,
#     'pipeline': {
#         'preprocs': [
#             'StandardScaler()',
#         ],
#         'learner': 'SVC(C=1.0)'
#     },
#     'metricName': 'Accuracy',
#     'metric_value': 0.90
# }
# add_new_workflow(data)