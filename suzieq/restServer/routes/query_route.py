from fastapi import APIRouter, Depends
from typing_extensions import Annotated

from suzieq.restServer.services.query_service import read_shared
from suzieq.restServer.models.query_models import (
    ArpndParams,
    BgpParams,
    DeviceParams,
    DevconfigParams,
    EvpnVniParams,
    FsParams,
    InterfaceParams,
    InventoryParams,
    LldpParams,
    MacParams,
    MlagParams,
    NetworkParams,
    NamespaceParams,
    OspfParams,
    PathParams,
    RouteParams,
    SqPollerParams,
    TopologyParams,
    TableParams,
    VlanParams,
)
from suzieq.restServer.utils.auth import REQUIRE_READ
from suzieq.restServer.utils.settings import get_config_file

router = APIRouter()


@router.get("/arpnd/{verb}", dependencies=[REQUIRE_READ])
def query_arpnd(
    params: Annotated[ArpndParams, Depends(ArpndParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("arpnd", params, config_file)


@router.get("/bgp/{verb}", dependencies=[REQUIRE_READ])
def query_bgp(
    params: Annotated[BgpParams, Depends(BgpParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("bgp", params, config_file)


@router.get("/device/{verb}", dependencies=[REQUIRE_READ])
def query_device(
    params: Annotated[DeviceParams, Depends(DeviceParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("device", params, config_file)


@router.get("/devconfig/{verb}", dependencies=[REQUIRE_READ])
def query_devconfig(
    params: Annotated[DevconfigParams, Depends(DevconfigParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("devconfig", params, config_file)


@router.get("/evpnVni/{verb}", dependencies=[REQUIRE_READ])
def query_evpnVni(
    params: Annotated[EvpnVniParams, Depends(EvpnVniParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("evpnVni", params, config_file)


@router.get("/fs/{verb}", dependencies=[REQUIRE_READ])
def query_fs(
    params: Annotated[FsParams, Depends(FsParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("fs", params, config_file)


@router.get("/interface/{verb}", dependencies=[REQUIRE_READ])
def query_interface(
    params: Annotated[InterfaceParams, Depends(InterfaceParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("interface", params, config_file)


@router.get("/inventory/{verb}", dependencies=[REQUIRE_READ])
def query_inventory(
    params: Annotated[InventoryParams, Depends(InventoryParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("inventory", params, config_file)


@router.get("/lldp/{verb}", dependencies=[REQUIRE_READ])
def query_lldp(
    params: Annotated[LldpParams, Depends(LldpParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("lldp", params, config_file)


@router.get("/mac/{verb}", dependencies=[REQUIRE_READ])
def query_mac(
    params: Annotated[MacParams, Depends(MacParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("mac", params, config_file)


@router.get("/mlag/{verb}", dependencies=[REQUIRE_READ])
def query_mlag(
    params: Annotated[MlagParams, Depends(MlagParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("mlag", params, config_file)


@router.get("/network/{verb}", dependencies=[REQUIRE_READ])
def query_network(
    params: Annotated[NetworkParams, Depends(NetworkParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("network", params, config_file)


@router.get("/namespace/{verb}", dependencies=[REQUIRE_READ])
def query_namespace(
    params: Annotated[NamespaceParams, Depends(NamespaceParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("namespace", params, config_file)


@router.get("/ospf/{verb}", dependencies=[REQUIRE_READ])
def query_ospf(
    params: Annotated[OspfParams, Depends(OspfParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("ospf", params, config_file)


@router.get("/path/{verb}", dependencies=[REQUIRE_READ])
def query_path(
    params: Annotated[PathParams, Depends(PathParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("path", params, config_file)


@router.get("/route/{verb}", dependencies=[REQUIRE_READ])
def query_route(
    params: Annotated[RouteParams, Depends(RouteParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("route", params, config_file)


@router.get("/sqPoller/{verb}", dependencies=[REQUIRE_READ])
def query_sqPoller(
    params: Annotated[SqPollerParams, Depends(SqPollerParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("sqPoller", params, config_file)


@router.get("/topology/{verb}", dependencies=[REQUIRE_READ])
def query_topology(
    params: Annotated[TopologyParams, Depends(TopologyParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("topology", params, config_file)


@router.get("/table/{verb}", dependencies=[REQUIRE_READ])
def query_table(
    params: Annotated[TableParams, Depends(TableParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("table", params, config_file)


@router.get("/vlan/{verb}", dependencies=[REQUIRE_READ])
def query_vlan(
    params: Annotated[VlanParams, Depends(VlanParams)],
    config_file: str = Depends(get_config_file),
):
    return read_shared("vlan", params, config_file)
