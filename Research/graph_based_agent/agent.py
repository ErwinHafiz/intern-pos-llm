import os
from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm

from google.adk import Agent
from google.adk import Workflow
from google.adk import Event
from pydantic import BaseModel

from google.adk.workflow import JoinNode

from ragflow_sdk import RAGFlow

from dotenv import load_dotenv
load_dotenv()  




rag_object = RAGFlow(api_key=os.getenv("RAGFLOW_API_KEY"), base_url=os.getenv("RAGFLOW_BASE_URL"))


def list_ragflow_datasets():
    """List all available RAGFlow datasets."""
    datasets = rag_object.list_datasets()
    return datasets

def lookup_ragflow_dataset(node_input: str):
    """"lookup a specific RAGFlow dataset by name."""
    dataset = list_ragflow_datasets()
    for ds in dataset:
        ds_name = ds.name if hasattr(ds, 'name') else ds.get('name')
        if ds_name == node_input:
            return ds
    return None



city_generator_agent = Agent(
    name="city_generator_agent",
    model=LiteLlm(
        model="openai/gpt-5.1",
        api_base=os.getenv("OPENAI_API_BASE"),
        api_key=os.getenv("OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION"),
    ),
    instruction="""Return the name of a random city.
    Return only the name, nothing else.""",
)

class CityTime(BaseModel):
    time_info: str  # time information
    city: str       # city name

def lookup_time_function(node_input: str):
    """Simulate returning the current time in the specified city."""
    return CityTime(time_info="10:10 AM", city=node_input)

city_report_agent = Agent(
    name="city_report_agent",
    model=LiteLlm(
            model="openai/gpt-5.1",
            api_base=os.getenv("OPENAI_API_BASE"),
            api_key=os.getenv("OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_API_VERSION"),
    ),
    input_schema=CityTime,
    instruction="""You receive a CityTime with time_info and city fields.
    Output a single line stating that it is that time in that city right
    now.""",
)

def completed_message_function(node_input: str):
    return Event(
        message=f"{node_input}\n WORKFLOW COMPLETED.",
    )


process_message = Agent(
    name="process_message",
    model=LiteLlm(
            model="openai/gpt-5.1",
            api_base=os.getenv("OPENAI_API_BASE"),
            api_key=os.getenv("OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_API_VERSION"),
    ),
    instruction="""Classify user message into either "BUG", "CUSTOMER_SUPPORT",
      "LOGISTICS" or "RAGFLOW". If you think a message applies to more than one category,
      reply with a comma separated list of categories.
   """,
   tools=[city_generator_agent, lookup_time_function, city_report_agent, completed_message_function,],
)

def router(node_input: str):
    routes = node_input.split(",")
    routes = [route.strip() for route in routes]
    return Event(route=routes)

def response_1_bug():
    return Event(message="Handling bug...")

def response_2_support():
    return Event(message="Handling customer support...")

def response_3_logistics():
    return Event(message="Handling logistics...")

# def response_4_ragflow(node_input):
#     """This function will be called when the router routes to RAGFLOW.
#     It will lookup the dataset in RAGFLOW and return the result.
#     """
#     dataset = lookup_ragflow_dataset(node_input)
#     if dataset is None:
#         return Event(message=f"Dataset '{node_input}' not found in RAGFLOW.")
    
#     # Here you can add more logic to interact with the dataset if needed.
#     return Event(message=f"Found dataset: {dataset['name']} with ID: {dataset['id']}")
def response_4_ragflow(node_input: str | None = None):
    """Called when router routes to RAGFLOW."""
    if not node_input or str(node_input) == "None":
        datasets = list_ragflow_datasets()
        names = [ds.name if hasattr(ds, "name") else ds.get("name") for ds in datasets]
        return Event(message=f"Routing to RAGFLOW. Available datasets: {names}")

    dataset = lookup_ragflow_dataset(node_input)
    if dataset is None:
        return Event(message=f"Dataset '{node_input}' not found in RAGFLOW.")

    ds_name = dataset.name if hasattr(dataset, "name") else dataset.get("name")
    ds_id = dataset.id if hasattr(dataset, "id") else dataset.get("id")
    return Event(message=f"Found dataset: {ds_name} with ID: {ds_id}")


def final_aggregator(node_input):
    # Lihat apa isi node_input yang dikirim oleh JoinNode!
    return Event(message=f"Hasil gabungan dari JoinNode:\n{node_input}")

# Konsep join owrkflow
join_node = JoinNode(
    name = "join_node"
)

root_agent = Workflow(
    name="join_routing_workflow",
    edges = [
        #1 try 
        ("START", process_message, router),

        #2 Cabang atau router
        (
            router,
            {
                "BUG": response_1_bug,
                "CUSTOMER_SUPPORT": response_2_support,
                "LOGISTICS": response_3_logistics,
                "RAGFLOW": response_4_ragflow,
            },
        ),

        #fan in dari cabang (tutup cabang)
        (response_1_bug, join_node),
        (response_2_support, join_node),
        (response_3_logistics, join_node),
        (response_4_ragflow, join_node),

        #proses final agregator dari tutup cabang
        (join_node, final_aggregator)
    ],

)




#konsep workflow routing
# root_agent = Workflow(
#    name="routing_workflow",
#    edges=[
#        ("START", process_message, router),
#        ( router,
#            {
#                "BUG": response_1_bug,
#                "CUSTOMER_SUPPORT": response_2_support,
#                "LOGISTICS": response_3_logistics,
#            }
#        )
#    ],
# )

# konsep workflow
# root_agent = Workflow(
#     name='root_agent',
#     edges =[
#         ("Start", city_generator_agent, lookup_time_function, city_report_agent, completed_message_function),
#     ]

# )
