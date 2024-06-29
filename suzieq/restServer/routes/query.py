from enum import Enum
from typing import List, Optional

from fastapi import Depends, APIRouter, Query
from pydantic import BaseModel
from typing_extensions import Annotated

from suzieq.restServer.services.query_services import read_shared
from suzieq.restServer.utils.auth import REQUIRE_READ

router = APIRouter()


class CommonVerbs(str, Enum):
    SHOW = "show"
    SUMMARIZE = "summarize"
    UNIQUE = "unique"
    TOP = "top"


class CommonExtraVerbs(str, Enum):
    AVER = "assert"
    SHOW = "show"
    SUMMARIZE = "summarize"
    UNIQUE = "unique"
    TOP = "top"


class RouteVerbs(str, Enum):
    SHOW = "show"
    SUMMARIZE = "summarize"
    UNIQUE = "unique"
    LPM = "lpm"
    TOP = "top"


class NetworkVerbs(str, Enum):
    FIND = "find"


class DeviceStatus(str, Enum):
    ALIVE = "alive"
    DEAD = "dead"
    NEVERPOLL = "neverpoll"
    NOTALIVE = "!alive"
    NOTDEAD = "!dead"
    NOTNEVERPOLL = "!neverpoll"


class BgpStateValues(str, Enum):
    ESTABLISHED = "Established"
    NOTESTD = "NotEstd"
    DYNAMIC = "dynamic"
    NOTESTABLISHED = "!Established"
    NOTNOTESTD = "!NotEstd"
    NOTDYNAMIC = "!dynamic"


class IfStateValues(str, Enum):
    UP = "up"
    DOWN = "down"
    ERRDISABLED = "errDisabled"
    NOTCONNECTED = "notConnected"
    NOTUP = "!up"
    NOTDOWN = "!down"
    NOTERRDISABLED = "!errDisabled"
    CONNECTED = "!notConnected"


class OspfStateValues(str, Enum):
    FULL = "full"
    PASSIVE = "passive"
    OTHER = "other"
    NOTFULL = "!full"
    NOTPASSIVE = "!passive"
    NOTOTHER = "!other"


class AssertResultValue(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    ALL = "all"


class SqPollerStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    ALL = "all"


class InventoryStatusValues(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"


class TruthasStrings(str, Enum):
    YES = "True"
    NO = "False"


class ViewValues(str, Enum):
    LATEST = "latest"
    ALL = "all"
    CHANGES = "changes"


class CommonParams(BaseModel):
    format: str
    hostname: Annotated[Optional[List[str]], Query()] = None
    start_time: Optional[str] = ""
    end_time: Optional[str] = ""
    view: Optional[ViewValues] = ViewValues.LATEST
    namespace: Annotated[Optional[List[str]], Query()] = None
    columns: Annotated[Optional[List[str]], Query()] = ["default"]
    query_str: Optional[str] = None
    what: Optional[str] = None
    count: Optional[str] = None
    reverse: Optional[str] = None


class ArpndParams(CommonParams):
    verb: CommonVerbs
    ipAddress: Annotated[Optional[List[str]], Query()] = None
    macaddr: Annotated[Optional[List[str]], Query()] = None
    prefix: Annotated[Optional[List[str]], Query()] = None
    oif: Annotated[Optional[List[str]], Query()] = None


@router.get("/arpnd/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_arpnd(params: Annotated[ArpndParams, Depends(ArpndParams)]):
    return read_shared("arpnd", params)


class BgpParams(CommonParams):
    verb: CommonExtraVerbs
    peer: Annotated[Optional[List[str]], Query()] = None
    state: Optional[BgpStateValues] = None
    vrf: Annotated[Optional[List[str]], Query()] = None
    asn: Annotated[Optional[List[str]], Query()] = None
    result: Optional[AssertResultValue] = None
    afiSafi: Optional[str] = None


@router.get("/bgp/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_bgp(params: Annotated[BgpParams, Depends(BgpParams)]):
    return read_shared("bgp", params)


class DeviceParams(CommonParams):
    verb: CommonVerbs
    os: Annotated[Optional[List[str]], Query()] = None
    vendor: Annotated[Optional[List[str]], Query()] = None
    model: Annotated[Optional[List[str]], Query()] = None
    version: Annotated[Optional[List[str]], Query()] = None
    status: Annotated[Optional[List[DeviceStatus]], Query()] = None
    ignore_neverpoll: Optional[bool] = None


@router.get("/device/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_device(params: Annotated[DeviceParams, Depends(DeviceParams)]):
    return read_shared("device", params)


class DevconfigParams(CommonParams):
    verb: CommonVerbs
    section: Optional[str] = None


@router.get("/devconfig/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_devconfig(params: Annotated[DevconfigParams, Depends(DevconfigParams)]):
    return read_shared("devconfig", params)


class EvpnVniParams(CommonParams):
    verb: CommonExtraVerbs
    vni: Annotated[Optional[List[str]], Query()] = None
    priVtepIp: Annotated[Optional[List[str]], Query()] = None
    result: Optional[AssertResultValue] = None


@router.get("/evpnVni/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_evpnVni(params: Annotated[EvpnVniParams, Depends(EvpnVniParams)]):
    return read_shared("evpnVni", params)


class FsParams(CommonParams):
    verb: CommonVerbs
    mountPoint: Annotated[Optional[List[str]], Query()] = None
    usedPercent: Optional[str] = None


@router.get("/fs/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_fs(params: Annotated[FsParams, Depends(FsParams)]):
    return read_shared("fs", params)


class InterfaceParams(CommonParams):
    verb: CommonExtraVerbs
    ifname: Annotated[Optional[List[str]], Query()] = None
    state: Optional[IfStateValues] = None
    type: Annotated[Optional[List[str]], Query()] = None
    vrf: Annotated[Optional[List[str]], Query()] = None
    master: Annotated[Optional[List[str]], Query()] = None
    mtu: Annotated[Optional[List[str]], Query()] = None
    ifindex: Annotated[Optional[List[str]], Query()] = None
    value: Optional[List[int]] = None
    result: Optional[AssertResultValue] = None
    ignore_missing_peer: Optional[bool] = False
    vlan: Annotated[Optional[List[str]], Query()] = None
    portmode: Annotated[Optional[List[str]], Query()] = None
    macaddr: Annotated[Optional[List[str]], Query()] = None
    bond: Annotated[Optional[List[str]], Query()] = None


@router.get("/interface/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_interface(params: Annotated[InterfaceParams, Depends(InterfaceParams)]):
    return read_shared("interface", params)


class InventoryParams(CommonParams):
    verb: CommonVerbs
    type: Annotated[Optional[List[str]], Query()] = None
    serial: Annotated[Optional[List[str]], Query()] = None
    model: Annotated[Optional[List[str]], Query()] = None
    vendor: Annotated[Optional[List[str]], Query()] = None
    status: Optional[InventoryStatusValues] = None


@router.get("/inventory/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_inventory(params: Annotated[InventoryParams, Depends(InventoryParams)]):
    return read_shared("inventory", params)


class LldpParams(CommonParams):
    verb: CommonVerbs
    peerMacaddr: Annotated[Optional[List[str]], Query()] = None
    peerHostname: Annotated[Optional[List[str]], Query()] = None
    ifname: Annotated[Optional[List[str]], Query()] = None
    use_bond: Optional[TruthasStrings] = None


@router.get("/lldp/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_lldp(params: Annotated[LldpParams, Depends(LldpParams)]):
    return read_shared("lldp", params)


class MacParams(CommonParams):
    verb: CommonVerbs
    bd: Optional[str] = None
    local: Optional[str] = None
    macaddr: Annotated[Optional[List[str]], Query()] = None
    remoteVtepIp: Annotated[Optional[List[str]], Query()] = None
    vlan: Annotated[Optional[List[str]], Query()] = None
    moveCount: Optional[str] = None


@router.get("/mac/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_mac(params: Annotated[MacParams, Depends(MacParams)]):
    return read_shared("mac", params)


class MlagParams(CommonParams):
    verb: CommonVerbs


@router.get("/mlag/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_mlag(params: Annotated[MlagParams, Depends(MlagParams)]):
    return read_shared("mlag", params)


class NetworkParams(CommonParams):
    verb: NetworkVerbs
    address: Annotated[Optional[List[str]], Query()] = None
    vlan: Optional[str] = ""
    vrf: Optional[str] = ""


@router.get("/network/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_network(params: Annotated[NetworkParams, Depends(NetworkParams)]):
    return read_shared("network", params)


class NamespaceParams(CommonParams):
    verb: CommonVerbs
    version: Optional[str] = ""
    model: Annotated[Optional[List[str]], Query()] = None
    vendor: Annotated[Optional[List[str]], Query()] = None
    os: Annotated[Optional[List[str]], Query()] = None


@router.get("/namespace/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_namespace(params: Annotated[NamespaceParams, Depends(NamespaceParams)]):
    return read_shared("namespace", params)


class OspfParams(CommonParams):
    verb: CommonExtraVerbs
    ifname: Annotated[Optional[List[str]], Query()] = None
    state: Optional[OspfStateValues] = None
    area: Annotated[Optional[List[str]], Query()] = None
    vrf: Annotated[Optional[List[str]], Query()] = None
    result: Optional[AssertResultValue] = None


@router.get("/ospf/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_ospf(params: Annotated[OspfParams, Depends(OspfParams)]):
    return read_shared("ospf", params)


class PathParams(CommonParams):
    verb: CommonVerbs
    vrf: Optional[str] = None
    dest: Optional[str] = None
    src: Optional[str] = None


@router.get("/path/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_path(params: Annotated[PathParams, Depends(PathParams)]):
    return read_shared("path", params)


class RouteParams(CommonParams):
    verb: RouteVerbs
    prefix: Annotated[Optional[List[str]], Query()] = None
    vrf: Annotated[Optional[List[str]], Query()] = None
    protocol: Annotated[Optional[List[str]], Query()] = None
    prefixlen: Optional[str] = None
    ipvers: Optional[str] = None
    add_filter: Optional[str] = None
    address: Optional[str] = None


@router.get("/route/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_route(params: Annotated[RouteParams, Depends(RouteParams)]):
    return read_shared("route", params)


class SqPollerParams(CommonParams):
    verb: CommonVerbs
    service: Optional[str] = None
    status: Optional[SqPollerStatus] = None
    pollExcdPeriodCount: Optional[str] = None


@router.get("/sqPoller/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_sqPoller(params: Annotated[SqPollerParams, Depends(SqPollerParams)]):
    return read_shared("sqPoller", params)


class TopologyParams(CommonParams):
    verb: CommonVerbs
    polled: Optional[str] = None
    via: Annotated[Optional[List[str]], Query()] = None
    ifname: Annotated[Optional[List[str]], Query()] = None
    peerHostname: Annotated[Optional[List[str]], Query()] = None
    asn: Annotated[Optional[List[str]], Query()] = None
    area: Annotated[Optional[List[str]], Query()] = None
    vrf: Annotated[Optional[List[str]], Query()] = None
    afiSafi: Optional[str] = None


@router.get("/topology/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_topology(params: Annotated[TopologyParams, Depends(TopologyParams)]):
    return read_shared("topology", params)


class TableParams(CommonParams):
    verb: CommonVerbs
    table: Optional[str] = None


@router.get("/table/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_table(params: Annotated[TableParams, Depends(TableParams)]):
    return read_shared("table", params)


class VlanParams(CommonParams):
    verb: CommonVerbs
    vlan: Annotated[Optional[List[str]], Query()] = None
    state: Optional[str] = None
    vlanName: Annotated[Optional[List[str]], Query()] = None


@router.get("/vlan/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_vlan(params: Annotated[VlanParams, Depends(VlanParams)]):
    return read_shared("vlan", params)
