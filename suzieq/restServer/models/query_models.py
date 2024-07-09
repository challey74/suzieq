from enum import Enum
from typing import List, Optional

from fastapi import Query
from pydantic import BaseModel
from typing_extensions import Annotated

from suzieq.shared.utils import DataFormats


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
    format: DataFormats = DataFormats.JSON
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


class BgpParams(CommonParams):
    verb: CommonExtraVerbs
    peer: Annotated[Optional[List[str]], Query()] = None
    state: Optional[BgpStateValues] = None
    vrf: Annotated[Optional[List[str]], Query()] = None
    asn: Annotated[Optional[List[str]], Query()] = None
    result: Optional[AssertResultValue] = None
    afiSafi: Optional[str] = None


class DeviceParams(CommonParams):
    verb: CommonVerbs
    os: Annotated[Optional[List[str]], Query()] = None
    vendor: Annotated[Optional[List[str]], Query()] = None
    model: Annotated[Optional[List[str]], Query()] = None
    version: Annotated[Optional[List[str]], Query()] = None
    status: Annotated[Optional[List[DeviceStatus]], Query()] = None
    ignore_neverpoll: Optional[bool] = None


class DevconfigParams(CommonParams):
    verb: CommonVerbs
    section: Optional[str] = None


class EvpnVniParams(CommonParams):
    verb: CommonExtraVerbs
    vni: Annotated[Optional[List[str]], Query()] = None
    priVtepIp: Annotated[Optional[List[str]], Query()] = None
    result: Optional[AssertResultValue] = None


class FsParams(CommonParams):
    verb: CommonVerbs
    mountPoint: Annotated[Optional[List[str]], Query()] = None
    usedPercent: Optional[str] = None


class InterfaceParams(CommonParams):
    verb: CommonExtraVerbs
    ifname: Annotated[Optional[List[str]], Query()] = None
    state: Optional[IfStateValues] = None
    type: Annotated[Optional[List[str]], Query()] = None
    vrf: Annotated[Optional[List[str]], Query()] = None
    master: Annotated[Optional[List[str]], Query()] = None
    mtu: Annotated[Optional[List[str]], Query()] = None
    ifindex: Annotated[Optional[List[str]], Query()] = None
    value: Annotated[Optional[List[int]], Query()] = None
    result: Optional[AssertResultValue] = None
    ignore_missing_peer: Optional[bool] = None
    vlan: Annotated[Optional[List[str]], Query()] = None
    portmode: Annotated[Optional[List[str]], Query()] = None
    macaddr: Annotated[Optional[List[str]], Query()] = None
    bond: Annotated[Optional[List[str]], Query()] = None


class InventoryParams(CommonParams):
    verb: CommonVerbs
    type: Annotated[Optional[List[str]], Query()] = None
    serial: Annotated[Optional[List[str]], Query()] = None
    model: Annotated[Optional[List[str]], Query()] = None
    vendor: Annotated[Optional[List[str]], Query()] = None
    status: Optional[InventoryStatusValues] = None


class LldpParams(CommonParams):
    verb: CommonVerbs
    peerMacaddr: Annotated[Optional[List[str]], Query()] = None
    peerHostname: Annotated[Optional[List[str]], Query()] = None
    ifname: Annotated[Optional[List[str]], Query()] = None
    use_bond: Optional[TruthasStrings] = None


class MacParams(CommonParams):
    verb: CommonVerbs
    bd: Optional[str] = None
    local: Optional[str] = None
    macaddr: Annotated[Optional[List[str]], Query()] = None
    remoteVtepIp: Annotated[Optional[List[str]], Query()] = None
    vlan: Annotated[Optional[List[str]], Query()] = None
    moveCount: Optional[str] = None


class MlagParams(CommonParams):
    verb: CommonVerbs


class NetworkParams(CommonParams):
    verb: NetworkVerbs
    address: Annotated[Optional[List[str]], Query()] = None
    vlan: Optional[str] = ""
    vrf: Optional[str] = ""


class NamespaceParams(CommonParams):
    verb: CommonVerbs
    version: Optional[str] = ""
    model: Annotated[Optional[List[str]], Query()] = None
    vendor: Annotated[Optional[List[str]], Query()] = None
    os: Annotated[Optional[List[str]], Query()] = None


class OspfParams(CommonParams):
    verb: CommonExtraVerbs
    ifname: Annotated[Optional[List[str]], Query()] = None
    state: Optional[OspfStateValues] = None
    area: Annotated[Optional[List[str]], Query()] = None
    vrf: Annotated[Optional[List[str]], Query()] = None
    result: Optional[AssertResultValue] = None


class PathParams(CommonParams):
    verb: CommonVerbs
    vrf: Optional[str] = None
    dest: Optional[str] = None
    src: Optional[str] = None


class RouteParams(CommonParams):
    verb: RouteVerbs
    prefix: Annotated[Optional[List[str]], Query()] = None
    vrf: Annotated[Optional[List[str]], Query()] = None
    protocol: Annotated[Optional[List[str]], Query()] = None
    prefixlen: Optional[str] = None
    ipvers: Optional[str] = None
    add_filter: Optional[str] = None
    address: Optional[str] = None


class SqPollerParams(CommonParams):
    verb: CommonVerbs
    service: Optional[str] = None
    status: Optional[SqPollerStatus] = None
    pollExcdPeriodCount: Optional[str] = None


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


class TableParams(CommonParams):
    verb: CommonVerbs
    table: Optional[str] = None


class VlanParams(CommonParams):
    verb: CommonVerbs
    vlan: Annotated[Optional[List[str]], Query()] = None
    state: Optional[str] = None
    vlanName: Annotated[Optional[List[str]], Query()] = None
