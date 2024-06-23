from enum import Enum
from typing import List, Optional

from fastapi import Depends, Query
from fastapi.router import APIRouter
from pydantic import BaseModel

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


class ViewValues(str, Enum):
    LATEST = "latest"
    ALL = "all"
    CHANGES = "changes"


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


class CommonParams(BaseModel):
    format: Optional[str] = None
    hostname: Optional[List[str]] = Query(None)
    start_time: Optional[str] = ""
    end_time: Optional[str] = ""
    view: Optional[ViewValues] = ViewValues.LATEST
    namespace: Optional[List[str]] = Query(None)
    columns: Optional[List[str]] = Query(default=["default"])
    query_str: Optional[str] = None
    what: Optional[str] = None
    count: Optional[str] = None
    reverse: Optional[str] = None

    class Config:
        orm_mode = True


class ArpndParams(CommonParams):
    verb: CommonVerbs
    ipAddress: Optional[List[str]] = Query(None)
    macaddr: Optional[List[str]] = Query(None)
    prefix: Optional[List[str]] = Query(None)
    oif: Optional[List[str]] = Query(None)


@router.get("/api/v2/arpnd/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_arpnd(params: ArpndParams):
    return read_shared("arpnd", params)


class BgpParams(CommonParams):
    verb: CommonExtraVerbs
    peer: Optional[List[str]] = Query(None)
    state: Optional[BgpStateValues] = Query(None)
    vrf: Optional[List[str]] = Query(None)
    asn: Optional[List[str]] = Query(None)
    result: Optional[AssertResultValue] = Query(None)
    afiSafi: Optional[str] = Query(None)


@router.get("/api/v2/bgp/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_bgp(params: BgpParams):
    return read_shared("bgp", params)


class DeviceParams(CommonParams):
    verb: CommonVerbs
    os: Optional[List[str]] = Query(None)
    vendor: Optional[List[str]] = Query(None)
    model: Optional[List[str]] = Query(None)
    version: Optional[List[str]] = Query(None)
    status: Optional[List[DeviceStatus]] = Query(None)
    ignore_neverpoll: Optional[bool] = None


@router.get("/api/v2/device/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_device(params: DeviceParams):
    if params.status:
        params.status = [x.value for x in params.status]
    return read_shared("device", params)


class DevconfigParams(CommonParams):
    verb: CommonVerbs
    section: Optional[str] = Query(None)


@router.get("/api/v2/devconfig/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_devconfig(params: DevconfigParams):
    return read_shared("devconfig", params)


class EvpnVniParams(CommonParams):
    verb: CommonExtraVerbs
    vni: Optional[List[str]] = Query(None)
    priVtepIp: Optional[List[str]] = Query(None)
    result: Optional[AssertResultValue] = None


@router.get("/api/v2/evpnVni/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_evpnVni(params: EvpnVniParams):
    return read_shared("evpnVni", params)


class FsParams(CommonParams):
    verb: CommonVerbs
    mountPoint: Optional[List[str]] = Query(None)
    usedPercent: Optional[str] = None


@router.get("/api/v2/fs/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_fs(params: FsParams):
    return read_shared("fs", params)


class InterfaceParams(CommonParams):
    verb: CommonExtraVerbs
    ifname: Optional[List[str]] = Query(None)
    state: Optional[IfStateValues] = Query(None)
    type: Optional[List[str]] = Query(None)
    vrf: Optional[List[str]] = Query(None)
    master: Optional[List[str]] = Query(None)
    mtu: Optional[List[str]] = Query(None)
    ifindex: Optional[List[str]] = Query(None)
    value: Optional[List[int]] = Query(None)
    result: Optional[AssertResultValue] = Query(None)
    ignore_missing_peer: Optional[bool] = Query(False)
    vlan: Optional[List[str]] = Query(None)
    portmode: Optional[List[str]] = Query(None)
    macaddr: Optional[List[str]] = Query(None)
    bond: Optional[List[str]] = Query(None)


@router.get("/api/v2/interface/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_interface(params: InterfaceParams):
    return read_shared("interface", params)


class InventoryParams(CommonParams):
    verb: CommonVerbs
    type: Optional[List[str]] = Query(None)
    serial: Optional[List[str]] = Query(None)
    model: Optional[List[str]] = Query(None)
    vendor: Optional[List[str]] = Query(None)
    status: Optional[InventoryStatusValues] = Query(None)


@router.get("/api/v2/inventory/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_inventory(params: InventoryParams):
    return read_shared("inventory", params)


class LldpParams(CommonParams):
    verb: CommonVerbs
    peerMacaddr: Optional[List[str]] = Query(None)
    peerHostname: Optional[List[str]] = Query(None)
    ifname: Optional[List[str]] = Query(None)
    use_bond: Optional[TruthasStrings] = Query(None)


@router.get("/api/v2/lldp/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_lldp(params: LldpParams):
    return read_shared("lldp", params)


class MacParams(CommonParams):
    verb: CommonVerbs
    bd: Optional[str] = None
    local: Optional[str] = None
    macaddr: Optional[List[str]] = Query(None)
    remoteVtepIp: Optional[List[str]] = Query(None)
    vlan: Optional[List[str]] = Query(None)
    moveCount: Optional[str] = None


@router.get("/api/v2/mac/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_mac(params: MacParams):
    return read_shared("mac", params)


class MlagParams(CommonParams):
    verb: CommonVerbs


@router.get("/api/v2/mlag/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_mlag(params: MlagParams):
    return read_shared("mlag", params)


class NetworkParams(CommonParams):
    verb: NetworkVerbs
    address: Optional[List[str]] = Query(None)
    vlan: Optional[str] = ""
    vrf: Optional[str] = ""


@router.get("/api/v2/network/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_network(params: NetworkParams):
    return read_shared("network", params)


class NamespaceParams(CommonParams):
    verb: CommonVerbs
    version: Optional[str] = ""
    model: Optional[List[str]] = Query(None)
    vendor: Optional[List[str]] = Query(None)
    os: Optional[List[str]] = Query(None)


@router.get("/api/v2/namespace/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_namespace(params: NamespaceParams):
    return read_shared("namespace", params)


class OspfParams(CommonParams):
    verb: CommonExtraVerbs
    ifname: Optional[List[str]] = Query(None)
    state: Optional[OspfStateValues] = Query(None)
    area: Optional[List[str]] = Query(None)
    vrf: Optional[List[str]] = Query(None)
    result: Optional[AssertResultValue] = None


@router.get("/api/v2/ospf/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_ospf(params: OspfParams):
    return read_shared("ospf", params)


class PathParams(CommonParams):
    verb: CommonVerbs
    vrf: Optional[str] = Query(None)
    dest: Optional[str] = Query(None)
    src: Optional[str] = Query(None)


@router.get("/api/v2/path/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_path(params: PathParams):
    return read_shared("path", params)


class RouteParams(CommonParams):
    verb: RouteVerbs
    prefix: Optional[List[str]] = Query(None)
    vrf: Optional[List[str]] = Query(None)
    protocol: Optional[List[str]] = Query(None)
    prefixlen: Optional[str] = None
    ipvers: Optional[str] = None
    add_filter: Optional[str] = None
    address: Optional[str] = None


@router.get("/api/v2/route/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_route(params: RouteParams):
    return read_shared("route", params)


class SqPollerParams(CommonParams):
    verb: CommonVerbs
    service: Optional[str] = None
    status: Optional[SqPollerStatus] = Query(None)
    pollExcdPeriodCount: Optional[str] = None


@router.get("/api/v2/sqPoller/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_sqPoller(params: SqPollerParams):
    return read_shared("sqPoller", params)


class TopologyParams(CommonParams):
    verb: CommonVerbs
    polled: Optional[str] = None
    via: Optional[List[str]] = Query(None)
    ifname: Optional[List[str]] = Query(None)
    peerHostname: Optional[List[str]] = Query(None)
    asn: Optional[List[str]] = Query(None)
    area: Optional[List[str]] = Query(None)
    vrf: Optional[List[str]] = Query(None)
    afiSafi: Optional[str] = Query(None)


@router.get("/api/v2/topology/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_topology(params: TopologyParams):
    return read_shared("topology", params)


class TableParams(CommonParams):
    verb: CommonVerbs
    table: Optional[str] = None


@router.get("/api/v2/table/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_table(params: TableParams):
    return read_shared("table", params)


class VlanParams(CommonParams):
    verb: CommonVerbs
    vlan: Optional[List[str]] = Query(None)
    state: Optional[str] = None
    vlanName: Optional[List[str]] = Query(None)


@router.get("/api/v2/vlan/{verb}", dependencies=[Depends(REQUIRE_READ)])
def query_vlan(params: VlanParams):
    return read_shared("vlan", params)
