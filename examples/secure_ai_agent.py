import os
import json
import asyncio
from typing import Dict, List, Any
from dotenv import load_dotenv
import logging
from javelin_sdk import (
    JavelinClient,
    JavelinConfig,
    Route,
    RouteNotFoundError,
    QueryResponse
)
load_dotenv()

def setup_javelin_route(javelin_client):
    route_name = "test_route_1"
    try:
        existing_route = javelin_client.get_route(route_name)
        return existing_route
    except RouteNotFoundError:
        route_data = {
            "name": route_name,
            "type": "chat",
            "enabled": True,
            "models": [
                {
                    "name": "gpt-3.5-turbo",
                    "provider": "openai",
                    "suffix": "/chat/completions",
                }
            ],
            "config": {
                "organization": "myusers",
                "rate_limit": 7,
                "retries": 3,
                "archive": True,
                "retention": 7,
                "budget": {
                    "enabled": True,
                    "annual": 100000,
                    "currency": "USD",
                },
                "dlp": {"enabled": True, "strategy": "Inspect", "action": "notify"},
            },
        }
        route = Route.parse_obj(route_data)
        try:
            javelin_client.create_route(route)
            print(f"Route '{route_name}' created successfully")
            return route
        except Exception as e:
            print(f"Failed to create route: {str(e)}")
            return None
    except Exception as e:
        print(f"Error checking for existing route: {str(e)}")
        return None

class SecureAIAgent:
    def __init__(self, config: Dict, javelin_config: JavelinConfig):
        self.config = config
        self.javelin_config = javelin_config
        self.setup_javelin_client()
        self.system_prompt = self.create_full_prompt()
        self.conversation_history = []

    def setup_javelin_client(self):
        self.javelin_client = JavelinClient(self.javelin_config)

    def create_full_prompt(self) -> str:
        nodes = self.config['nodes']
        edges = self.config.get('edges', [])
        
        node_prompts = [f"Node {node['id']}:\n{node['prompt']}\n" for node in nodes]
        edge_prompts = [f"Edge {edge['id']} (from {edge['source_node']} to {edge['target_node']}):\n{edge['prompt']}\n" for edge in edges]
        
        full_prompt = f"""
{self.config['main_prompt']}

Available nodes and their tasks:
{"".join(node_prompts)}

Conversation flow (edges):
{"".join(edge_prompts)}

Your task:
1. Understand the user's intent and the current stage of the conversation.
2. Process the appropriate node based on the conversation flow.
3. Provide a response to the user, handling all necessary steps for the current node.
4. Use the edge information to determine when and how to transition between nodes.

Remember to stay in character throughout the conversation.
Starting node: {self.config['starting_node']}
"""
        return full_prompt

    async def process_message(self, message: str) -> str:
        self.conversation_history.append({"role": "user", "content": message})

        try:
            query_data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    *self.conversation_history
                ],
                "temperature": 0.7,
            }

            response: QueryResponse = self.javelin_client.query_route("test_route_1", query_data)
            ai_message = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": ai_message})

            return ai_message
        except RouteNotFoundError:
            logging.error("Route 'test_route_1' not found. Attempting to recreate...")
            setup_javelin_route(self.javelin_client)
            raise
        except Exception as e:
            logging.error(f"Error in process_message: {str(e)}")
            raise

async def main():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'graph_config.json'), 'r') as f:
            config = json.load(f)

        javelin_api_key = os.getenv("JAVELIN_API_KEY")
        javelin_virtualapikey = os.getenv("JAVELIN_VIRTUALAPIKEY")
        llm_api_key = os.getenv("LLM_API_KEY")  # Note: This is different from OPENAI_API_KEY

        javelin_config = JavelinConfig(
            base_url="https://api-dev.javelin.live",
            javelin_api_key=javelin_api_key,
            javelin_virtualapikey=javelin_virtualapikey,
            llm_api_key=llm_api_key,
        )
        agent = SecureAIAgent(config, javelin_config)
        route = setup_javelin_route(agent.javelin_client)
        
        if not route:
            print("Failed to set up the route. Exiting.")
            return

        print("Secure AI Agent System")
        print("Type 'exit' to end the conversation")

        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                break

            try:
                response = await agent.process_message(user_input)
                print(f"AI: {response}")
            except RouteNotFoundError:
                print("Error: The route 'test_route_1' was not found. Please check your Javelin configuration.")
                break
            except Exception as e:
                print(f"Error processing message: {str(e)}")
                break

    except Exception as e:
        logging.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())