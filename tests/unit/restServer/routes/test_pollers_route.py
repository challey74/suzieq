import pytest

from fastapi.testclient import TestClient

from unittest.mock import MagicMock, patch
from suzieq.poller.orchestrator.orchestrator import Orchestrator
from suzieq.restServer.utils.settings import Settings
from suzieq.restServer.models.poller_models import (
    PollerRequest,
    PollerRequestWithWebhook,
    PollerArgs,
    WebhookConfig,
)
from suzieq.restServer.routes.pollers_route import router

client = TestClient(router)


@pytest.fixture
def mock_orchestrator():
    return MagicMock(spec=Orchestrator)


@pytest.fixture
def mock_settings():
    return MagicMock(spec=Settings)


def test_create_poller(mock_settings):
    request = PollerRequest()
    with patch(
        "suzieq.restServer.services.poller_services.create_controller"
    ) as mock_create_controller:
        mock_create_controller.return_value = {"id": 1}
        response = client.post("/pollers", json=request.dict())
        assert response.status_code == 200
        assert response.json() == {"id": 1}
        mock_create_controller.assert_called_once_with(request, mock_settings)


def test_create_poller_error(mock_settings):
    request = PollerRequest()
    with patch(
        "suzieq.restServer.services.poller_services.create_controller"
    ) as mock_create_controller:
        mock_create_controller.side_effect = Exception("Some error")
        response = client.post("/pollers", json=request.dict())
        assert response.status_code == 500
        assert response.json() == {"detail": "Some error"}


def test_create_and_start_poller(mock_orchestrator, mock_settings):
    request = PollerRequestWithWebhook()
    with patch(
        "suzieq.restServer.services.poller_services.create_controller"
    ) as mock_create_controller:
        mock_create_controller.return_value = {"id": 1}
        with patch(
            "suzieq.restServer.services.poller_services.start_controller"
        ) as mock_start_controller:
            mock_start_controller.return_value = {"id": 1, "status": "running"}
            response = client.post("/pollers/start", json=request.dict())
            assert response.status_code == 200
            assert response.json() == {"id": 1, "status": "running"}
            mock_create_controller.assert_called_once_with(request, mock_settings)
            mock_start_controller.assert_called_once_with(
                1, mock_orchestrator, request.webhook
            )


def test_create_and_start_poller_error(mock_orchestrator, mock_settings):
    request = PollerRequestWithWebhook()
    with patch(
        "suzieq.restServer.services.poller_services.create_controller"
    ) as mock_create_controller:
        mock_create_controller.side_effect = Exception("Some error")
        response = client.post("/pollers/start", json=request.dict())
        assert response.status_code == 500
        assert response.json() == {"detail": "Some error"}


def test_update_poller(mock_settings):
    poller_id = 1
    args = PollerArgs()
    with patch(
        "suzieq.restServer.services.poller_services.update_controller"
    ) as mock_update_controller:
        mock_update_controller.return_value = {"id": poller_id, "status": "updated"}
        response = client.patch(f"/pollers/{poller_id}", json=args.dict())
        assert response.status_code == 200
        assert response.json() == {"id": poller_id, "status": "updated"}
        mock_update_controller.assert_called_once_with(poller_id, args, mock_settings)


def test_update_poller_error(mock_settings):
    poller_id = 1
    args = PollerArgs()
    with patch(
        "suzieq.restServer.services.poller_services.update_controller"
    ) as mock_update_controller:
        mock_update_controller.side_effect = Exception("Some error")
        response = client.patch(f"/pollers/{poller_id}", json=args.dict())
        assert response.status_code == 500
        assert response.json() == {"detail": "Some error"}


def test_delete_poller(mock_orchestrator):
    poller_id = 1
    with patch(
        "suzieq.restServer.services.poller_services.delete_controller"
    ) as mock_delete_controller:
        mock_delete_controller.return_value = {"id": poller_id, "status": "deleted"}
        response = client.delete(f"/pollers/{poller_id}")
        assert response.status_code == 200
        assert response.json() == {"id": poller_id, "status": "deleted"}
        mock_delete_controller.assert_called_once_with(poller_id, mock_orchestrator)


def test_delete_poller_error(mock_orchestrator):
    poller_id = 1
    with patch(
        "suzieq.restServer.services.poller_services.delete_controller"
    ) as mock_delete_controller:
        mock_delete_controller.side_effect = Exception("Some error")
        response = client.delete(f"/pollers/{poller_id}")
        assert response.status_code == 500
        assert response.json() == {"detail": "Some error"}


def test_start_poller(mock_orchestrator):
    poller_id = 1
    webhook_config = WebhookConfig()
    with patch(
        "suzieq.restServer.services.poller_services.start_controller"
    ) as mock_start_controller:
        mock_start_controller.return_value = {"id": poller_id, "status": "running"}
        response = client.post(
            f"/pollers/{poller_id}/start", json=webhook_config.dict()
        )
        assert response.status_code == 200
        assert response.json() == {"id": poller_id, "status": "running"}
        mock_start_controller.assert_called_once_with(
            poller_id, mock_orchestrator, webhook_config
        )


def test_start_poller_error(mock_orchestrator):
    poller_id = 1
    webhook_config = WebhookConfig()
    with patch(
        "suzieq.restServer.services.poller_services.start_controller"
    ) as mock_start_controller:
        mock_start_controller.side_effect = Exception("Some error")
        response = client.post(
            f"/pollers/{poller_id}/start", json=webhook_config.dict()
        )
        assert response.status_code == 500
        assert response.json() == {"detail": "Some error"}


def test_stop_poller(mock_orchestrator):
    poller_id = 1
    with patch(
        "suzieq.restServer.services.poller_services.stop_controller"
    ) as mock_stop_controller:
        mock_stop_controller.return_value = {"id": poller_id, "status": "stopped"}
        response = client.post(f"/pollers/{poller_id}/stop")
        assert response.status_code == 200
        assert response.json() == {"id": poller_id, "status": "stopped"}
        mock_stop_controller.assert_called_once_with(poller_id, mock_orchestrator)


def test_stop_poller_error(mock_orchestrator):
    poller_id = 1
    with patch(
        "suzieq.restServer.services.poller_services.stop_controller"
    ) as mock_stop_controller:
        mock_stop_controller.side_effect = Exception("Some error")
        response = client.post(f"/pollers/{poller_id}/stop")
        assert response.status_code == 500
        assert response.json() == {"detail": "Some error"}


def test_read_pollers(mock_orchestrator):
    poller_ids = [1, 2]
    names = ["poller1", "poller2"]
    with patch(
        "suzieq.restServer.services.poller_services.read_controller"
    ) as mock_read_controller:
        mock_read_controller.return_value = [{"id": 1}, {"id": 2}]
        response = client.get("/pollers", params={"id": poller_ids, "name": names})
        assert response.status_code == 200
        assert response.json() == [{"id": 1}, {"id": 2}]
        mock_read_controller.assert_called_once_with(
            mock_orchestrator, poller_ids, names
        )


def test_read_pollers_error(mock_orchestrator):
    poller_ids = [1, 2]
    names = ["poller1", "poller2"]
    with patch(
        "suzieq.restServer.services.poller_services.read_controller"
    ) as mock_read_controller:
        mock_read_controller.side_effect = Exception("Some error")
        response = client.get("/pollers", params={"id": poller_ids, "name": names})
        assert response.status_code == 500
        assert response.json() == {"detail": "Some error"}


def test_read_poller(mock_orchestrator):
    poller_id = 1
    with patch(
        "suzieq.restServer.services.poller_services.read_controller"
    ) as mock_read_controller:
        mock_read_controller.return_value = [{"id": poller_id}]
        response = client.get(f"/pollers/{poller_id}")
        assert response.status_code == 200
        assert response.json() == [{"id": poller_id}]
        mock_read_controller.assert_called_once_with(mock_orchestrator, [poller_id])


def test_read_poller_error(mock_orchestrator):
    poller_id = 1
    with patch(
        "suzieq.restServer.services.poller_services.read_controller"
    ) as mock_read_controller:
        mock_read_controller.side_effect = Exception("Some error")
        response = client.get(f"/pollers/{poller_id}")
        assert response.status_code == 500
        assert response.json() == {"detail": "Some error"}
