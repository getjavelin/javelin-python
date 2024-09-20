import pytest
import uuid
from javelin_sdk.models import Gateway, GatewayConfig
from javelin_sdk.exceptions import GatewayNotFoundError, GatewayAlreadyExistsError, BadRequest

@pytest.fixture
async def test_gateway(javelin_client):
    unique_name = f"test_gateway_{uuid.uuid4().hex[:8]}"
    gateway_config = GatewayConfig(
        buid="test_buid",
        base_url="https://test.com",
        api_key_value="test_api_key",
        organization_id="test_org",
        system_namespace="test_namespace"
    )
    gateway = Gateway(
        name=unique_name,
        type="development",
        enabled=True,
        config=gateway_config
    )
    await javelin_client.acreate_gateway(gateway)
    yield gateway
    try:
        await javelin_client.adelete_gateway(unique_name)
    except GatewayNotFoundError:
        pass

@pytest.mark.asyncio
async def test_create_gateway(javelin_client):
    unique_name = f"test_gateway_{uuid.uuid4().hex[:8]}"
    gateway_config = GatewayConfig(
        buid="test_buid",
        base_url="https://test.com",
        api_key_value="test_api_key",
        organization_id="test_org",
        system_namespace="test_namespace"
    )
    gateway = Gateway(
        name=unique_name,
        type="development",
        enabled=True,
        config=gateway_config
    )
    created_gateway = await javelin_client.acreate_gateway(gateway)
    assert "gateway created successfully" in created_gateway.lower()
    
    # Clean up
    await javelin_client.adelete_gateway(unique_name)

@pytest.mark.asyncio
async def test_get_gateway(javelin_client, test_gateway):
    gateway = await test_gateway
    retrieved_gateway = await javelin_client.aget_gateway(gateway.name)
    assert retrieved_gateway.name == gateway.name

@pytest.mark.asyncio
async def test_update_gateway(javelin_client, test_gateway):
    gateway = await test_gateway
    gateway.config.base_url = "https://updated.com"
    updated_gateway = await javelin_client.aupdate_gateway(gateway)
    assert "gateway updated successfully" in updated_gateway.lower()

    retrieved_gateway = await javelin_client.aget_gateway(gateway.name)
    assert retrieved_gateway.config.base_url == "https://updated.com"

@pytest.mark.asyncio
async def test_delete_gateway(javelin_client):
    unique_name = f"test_gateway_{uuid.uuid4().hex[:8]}"
    gateway_config = GatewayConfig(
        buid="test_buid",
        base_url="https://test.com",
        api_key_value="test_api_key",
        organization_id="test_org",
        system_namespace="test_namespace"
    )
    gateway = Gateway(
        name=unique_name,
        type="development",
        enabled=True,
        config=gateway_config
    )
    await javelin_client.acreate_gateway(gateway)

    deleted_gateway = await javelin_client.adelete_gateway(unique_name)
    assert "gateway deleted successfully" in deleted_gateway.lower()

    with pytest.raises(GatewayNotFoundError):
        await javelin_client.aget_gateway(unique_name)

@pytest.mark.asyncio
async def test_list_gateways(javelin_client, test_gateway):
    gateway = await test_gateway
    gateways = await javelin_client.alist_gateways()
    assert isinstance(gateways.gateways, list)
    assert any(g.name == gateway.name for g in gateways.gateways)

@pytest.mark.asyncio
async def test_create_duplicate_gateway(javelin_client, test_gateway):
    gateway = await test_gateway
    with pytest.raises((GatewayAlreadyExistsError, BadRequest)):
        await javelin_client.acreate_gateway(gateway)

@pytest.mark.asyncio
@pytest.mark.parametrize("gateway_type", ["development", "production"])
async def test_create_gateway_types(javelin_client, gateway_type):
    unique_name = f"test_gateway_{uuid.uuid4().hex[:8]}"
    gateway_config = GatewayConfig(
        buid="test_buid",
        base_url="https://test.com",
        api_key_value="test_api_key",
        organization_id="test_org",
        system_namespace="test_namespace"
    )
    gateway = Gateway(
        name=unique_name,
        type=gateway_type,
        enabled=True,
        config=gateway_config
    )
    created_gateway = await javelin_client.acreate_gateway(gateway)
    assert "gateway created successfully" in created_gateway.lower()
    
    # Clean up
    await javelin_client.adelete_gateway(unique_name)