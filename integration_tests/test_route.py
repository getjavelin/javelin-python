import pytest
import asyncio
import uuid
import json
from javelin_sdk import Route
from javelin_sdk.exceptions import RouteNotFoundError, RouteAlreadyExistsError, UnauthorizedError, NetworkError, BadRequest

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_route(javelin_client):
    unique_name = f"test_route_{uuid.uuid4().hex[:8]}"
    route_data = {
        "name": unique_name,
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
    await javelin_client.acreate_route(route)
    yield route
    try:
        await javelin_client.adelete_route(unique_name)
    except RouteNotFoundError:
        pass

@pytest.mark.asyncio
async def test_create_route(javelin_client):
    unique_name = f"test_route_{uuid.uuid4().hex[:8]}"
    route_data = {
        "name": unique_name,
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
    created_route = await javelin_client.acreate_route(route)
    created_route_json = json.loads(created_route)
    assert created_route_json["message"].lower() == "route created successfully"

    # Clean up
    await javelin_client.adelete_route(unique_name)

@pytest.mark.asyncio
async def test_query_route(javelin_client, test_route):
    # Get the Route object from the test_route fixture
    route: Route = await anext(test_route)
    
    # Extract the route name from the Route object
    route_name: str = route.name
    
    query_data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ],
        "temperature": 0.8,
    }
    
    try:
        response = await javelin_client.aquery_route(route_name, query_data)
        assert "choices" in response
        assert len(response["choices"]) > 0
    except RouteNotFoundError:
        pytest.skip("Route not found. Skipping test.")

@pytest.mark.asyncio
async def test_list_routes(javelin_client):
    routes = await javelin_client.alist_routes()
    assert isinstance(routes.routes, list)

@pytest.mark.asyncio
async def test_get_route(javelin_client, test_route):
    route: Route = await anext(test_route)
    retrieved_route = await javelin_client.aget_route(route.name)
    assert retrieved_route.name == route.name
    assert retrieved_route.type == "chat"
    assert retrieved_route.config.retries == 3

@pytest.mark.asyncio
async def test_update_route(javelin_client, test_route):
    route: Route = await anext(test_route)
    route.config.retries = 5
    updated_route = await javelin_client.aupdate_route(route)
    updated_route_json = json.loads(updated_route)
    assert updated_route_json["message"].lower() == "route updated successfully"

    retrieved_route = await javelin_client.aget_route(route.name)
    assert retrieved_route.config.retries == 5

@pytest.mark.asyncio
async def test_delete_route(javelin_client):
    unique_name = f"test_route_{uuid.uuid4().hex[:8]}"
    route_data = {
        "name": unique_name,
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
    await javelin_client.acreate_route(route)

    deleted_route = await javelin_client.adelete_route(unique_name)
    deleted_route_json = json.loads(deleted_route)
    assert deleted_route_json["message"].lower() == "route deleted successfully"

    with pytest.raises(RouteNotFoundError):
        await javelin_client.aget_route(unique_name)

@pytest.mark.asyncio
async def test_route_not_found(javelin_client):
    non_existent_route = f"non_existent_route_{uuid.uuid4().hex[:8]}"
    with pytest.raises(RouteNotFoundError):
        await javelin_client.aget_route(non_existent_route)

@pytest.mark.asyncio
async def test_create_duplicate_route(javelin_client, test_route):
    route: Route = await anext(test_route)
    with pytest.raises((RouteAlreadyExistsError, BadRequest)):
        await javelin_client.acreate_route(route)

@pytest.mark.parametrize("route_type", ["chat", "completion", "embedding"])
@pytest.mark.asyncio
async def test_create_route_types(javelin_client, route_type):
    unique_name = f"test_route_{uuid.uuid4().hex[:8]}"
    route_data = {
        "name": unique_name,
        "type": route_type,
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
    created_route = await javelin_client.acreate_route(route)
    created_route_json = json.loads(created_route)
    assert created_route_json["message"].lower() == "route created successfully"

    # Clean up
    await javelin_client.adelete_route(unique_name)
