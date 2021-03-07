import numpy as np
from dateparser import parse
from datetime import datetime
from copy import deepcopy

from suzieq.poller.services.service import Service
from suzieq.utils import get_timestamp_from_cisco_time
from suzieq.utils import get_timestamp_from_junos_time


class BgpService(Service):
    """bgp service. Different class because of munging of output across NOS"""

    def _clean_eos_data(self, processed_data, raw_data):

        for entry in processed_data:
            if entry["bfdStatus"] == 3:
                entry["bfdStatus"] = "up"
            elif entry["bfdStatus"] != "disabled":
                entry["bfdStatus"] = "down"
            entry["asn"] = int(entry["asn"])
            entry["peerAsn"] = int(entry["peerAsn"])
            entry['estdTime'] = raw_data[0]['timestamp'] - \
                (entry['estdTime']*1000)
            entry['origPeer'] = entry['peer']

        return processed_data

    def _clean_junos_data(self, processed_data, raw_data):

        peer_uptimes = {}
        drop_indices = []
        new_entries = []

        for i, entry in enumerate(processed_data):
            if entry['_entryType'] == 'summary':
                peer_uptimes[entry['peer']] = entry['estdTime']
                drop_indices.append(i)
                continue

            # JunOS adds entries which includes the port as IP+Port
            entry['peerIP'] = entry['peerIP'].split('+')[0]
            entry['peer'] = entry['peer'].split('+')[0]
            entry['updateSource'] = entry['updateSource'].split('+')[0]
            entry['numChanges'] = int(entry['numChanges'])
            entry['updatesRx'] = int(entry['updatesRx'])
            entry['updatesTx'] = int(entry['updatesTx'])
            entry['asn'] = int(entry['asn'])
            entry['peerAsn'] = int(entry['peerAsn'])
            entry['keepaliveTime'] = int(entry['keepaliveTime'])
            entry['holdTime'] = int(entry['holdTime'])

            if entry['peer'] in peer_uptimes:
                entry['estdTime'] = peer_uptimes[entry['peer']]
            else:
                entry['estdTime'] = '0d 00:00:00'

            advafis = set(entry['afiSafiAdvList'].split())
            rcvafis = set(entry['afiSafiRcvList'].split())

            entry['afisAdvOnly'] = list(advafis.difference(rcvafis))
            entry['afisRcvOnly'] = list(rcvafis.difference(advafis))
            entry['afisAdvOnly'] = [x.replace('-', ' ')
                                     .replace('inet', 'ipv4')
                                     .replace('inet6', 'ipv6')
                                     .replace('evpn', 'l2vpn evpn')
                                    for x in entry['afisAdvOnly']]
            entry['afisRcvOnly'] = [x.replace('-', ' ')
                                     .replace('inet', 'ipv4')
                                     .replace('inet6', 'ipv6')
                                     .replace('evpn', 'l2vpn evpn')
                                    for x in entry['afisRcvOnly']]

            # Junos doesn't provide this data in neighbor, only in summary
            entry['estdTime'] = get_timestamp_from_junos_time(
                entry['estdTime'], raw_data[0]['timestamp']/1000)

            if not entry.get('vrf', None):
                entry['vrf'] = 'default'

            if entry['state'] != 'Established':
                entry.pop('afiPrefix')
                entry.pop('pfxRcvd')
                entry.pop('pfxSent')
                entry.pop('sendComm')
                entry.pop('extendComm')
                entry.pop('defaultOrig')
                continue

            # Build the mapping between pfx counts with the AFI/SAFI
            # Assign counts to appropriate AFi/SAFI
            table_afi_map = {}
            for x in zip(entry['_tableAfiList'], entry['_tableNameList']):
                table_afi_map.setdefault(x[0], []).append(x[1])

            pfxrx_list = dict(zip(entry['_pfxType'], entry['_pfxRxList']))
            pfxtx_list = dict(zip(entry['_pfxType'], entry['_pfxTxList']))
            pfxsupp_list = dict(
                zip(entry['_pfxType'], entry['_pfxSuppressList']))
            pfxbest_list = dict(
                zip(entry['_pfxType'], entry['_pfxBestRxList']))

            for elem in table_afi_map:
                new_entry = deepcopy(entry)
                afi, safi = (elem.replace('-', ' ')
                             .replace('inet', 'ipv4')
                             .replace('inet6', 'ipv6')
                             .replace('evpn', 'l2vpn evpn')).split()
                new_entry['afi'] = afi
                new_entry['safi'] = safi
                new_entry['pfxRx'] = 0
                new_entry['pfxTx'] = 0
                new_entry['pfxBestRx'] = 0
                new_entry['pfxSuppressRx'] = 0
                for table in table_afi_map[elem]:
                    new_entry['pfxRx'] += int(pfxrx_list.get(table, 0) or 0)
                    new_entry['pfxTx'] += int(pfxtx_list.get(table, 0) or 0)
                    new_entry['pfxSuppressRx'] += int(pfxsupp_list.get(table, 0)
                                                      or 0)
                    new_entry['pfxBestRx'] += int(
                        pfxbest_list.get(table, 0) or 0)
                new_entry['communityTypes'] = ['standard', 'extended']

                new_entry.pop('_pfxType')
                new_entry.pop('_pfxRxList')
                new_entry.pop('_pfxTxList')
                new_entry.pop('_pfxSuppressList')
                new_entry.pop('_tableAfiList')
                new_entry.pop('_tableNameList')
                new_entries.append(new_entry)

            drop_indices.append(i)

        processed_data += new_entries
        processed_data = np.delete(processed_data, drop_indices).tolist()
        return processed_data

    def _clean_nxos_data(self, processed_data, raw_data):

        entries_by_vrf = {}
        drop_indices = []
        new_entries = []        # To add the AFI/SAFI-based entries

        for i, entry in enumerate(processed_data):
            if entry['_entryType'] == 'summary':
                for ventry in entries_by_vrf.get(entry['vrf'], []):
                    ventry['asn'] = entry['asn']
                    ventry['routerId'] = entry['routerId']
                drop_indices.append(i)
                continue

            if (entry.get('extnhAdvertised', False) == "true" and
                    entry.get('extnhReceived', False) == "true"):
                entry['extnhEnabled'] = True
            else:
                entry['extnhEnabled'] = False

            entry['estdTime'] = get_timestamp_from_cisco_time(
                entry['estdTime'], raw_data[0]['timestamp']/1000)
            if entry['vrf'] not in entries_by_vrf:
                entries_by_vrf[entry['vrf']] = []

            if not entry['peer']:
                if not entry.get('_dynPeer', None):
                    drop_indices.append(i)
                    continue
                entry['peer'] = entry['_dynPeer'].replace('/', '-')
                entry['origPeer'] = entry['_dynPeer']
                entry['state'] = 'dynamic'
                entry['v4PfxRx'] = entry['_activePeers']
                entry['v4PfxTx'] = entry['_maxconcurrentpeers']
                entry['estdTime'] = entry['_firstconvgtime']

            entry['afisAdvOnly'] = []
            entry['afisRcvOnly'] = []
            for i, item in enumerate(entry['afiSafi']):
                if entry['afAdvertised'][i] != entry['afRcvd'][i]:
                    if entry['afAdvertised'][i] == 'true':
                        entry['afisAdvOnly'].append(entry['afiSafi'])
                    else:
                        entry['afisRcvOnly'].append(entry['afiSafi'])

            entry.pop('afiSafi')
            entry.pop('afAdvertised')
            entry.pop('afRcvd')

            if entry['state'] != 'Established':
                entry.pop('afiPrefix')
                entry.pop('pfxRcvd')
                entry.pop('pfxSent')
                entry.pop('sendComm')
                entry.pop('extendComm')
                entry.pop('defaultOrig')
                entries_by_vrf[entry['vrf']].append(entry)
                continue

            entry['rrclient'] = entry.get('rrclient', False) == "true"

            defint_list = [0]*len(entry.get('afiPrefix', []))
            defbool_list = [False]*len(entry.get('afiPrefix', []))
            defstr_list = [""]*len(entry.get('afiPrefix', []))
            pfxRx_list = entry.get('pfxRcvd', []) or defint_list
            pfxTx_list = entry.get('pfxSent', []) or defint_list
            deforig_list = entry.get('defaultOrig', []) or defbool_list
            extcomm_list = entry.get('extendComm', []) or defbool_list
            comm_list = entry.get('sendComm', []) or defbool_list
            withdrawn_list = entry.get('pfxWithdrawn', []) or defint_list
            softrecon_list = entry.get('softReconfig', []) or defbool_list
            irmap_list = entry.get('ingressRmap', []) or defstr_list
            ermap_list = entry.get('egressRmap', []) or defstr_list

            for i, item in enumerate(entry['afiPrefix']):
                new_entry = deepcopy(entry)
                new_entry['afi'], new_entry['safi'] = \
                    [x.lower() for x in item.split()]
                new_entry['pfxRx'] = pfxRx_list[i]
                new_entry['pfxTx'] = pfxTx_list[i]
                new_entry['pfxWithdrawn'] = withdrawn_list[i]
                new_entry['softReconfig'] = softrecon_list[i]
                new_entry['defOriginate'] = deforig_list[i]
                new_entry['communityTypes'] = []
                if comm_list[i]:
                    new_entry['communityTypes'].append('standard')
                if extcomm_list[i] == "true":
                    new_entry['communityTypes'].append('extended')
                new_entry['ingressRmap'] = irmap_list[i]
                new_entry['egressRmap'] = ermap_list[i]
                new_entry.pop('afiPrefix')
                new_entry.pop('pfxRcvd')
                new_entry.pop('pfxSent')
                new_entry.pop('sendComm')
                new_entry.pop('extendComm')
                new_entry.pop('defaultOrig')

                new_entries.append(new_entry)
                entries_by_vrf[new_entry['vrf']].append(new_entry)
                drop_indices.append(i)

        processed_data += new_entries
        processed_data = np.delete(processed_data, drop_indices).tolist()
        return processed_data

    def _clean_iosxr_data(self, processed_data, raw_data):

        drop_indices = []
        vrf_rtrid = {}

        # The last two entries are routerIds. Extract them first
        for i, entry in enumerate(reversed(processed_data)):
            if not entry.get('_entryType', ''):
                break

            vrf_rtrid.update({entry.get('vrf', 'default') or 'default':
                              entry.get('routerId', '')})

        for i, entry in enumerate(processed_data):
            if entry.get('_entryType', ''):
                drop_indices.append(i)
                continue

            if entry.get('state', '') != 'Established':
                entry['state'] = 'NotEstd'

            entry['numChanges'] = (int(entry.get('_numConnEstd', 0) or 0) +
                                   int(entry.get('_numConnDropped', 0) or 0))
            if not entry.get('vrf', ''):
                entry['vrf'] = 'default'
            if entry.get('afi', ''):
                entry['afi'] = entry['afi'].lower()
            if entry.get('safi', ''):
                entry['safi'] = entry['safi'].lower()
            estdTime = parse(
                entry.get('estdTime', ''),
                settings={'RELATIVE_BASE':
                          datetime.fromtimestamp(
                              (raw_data[0]['timestamp'])/1000), })
            if estdTime:
                entry['estdTime'] = int(estdTime.timestamp()*1000)
            entry['routerId'] = vrf_rtrid.get(entry['vrf'], '')

        processed_data = np.delete(processed_data, drop_indices).tolist()
        return processed_data

    def _clean_cumulus_data(self, processed_data, raw_data):

        new_entries = []
        drop_indices = []

        for i, entry in enumerate(processed_data):
            if entry['state'] != 'Established':
                continue
            for afi in entry.get('_afiInfo', {}):
                new_entry = deepcopy(entry)
                if 'evpn' in afi.lower():
                    new_entry['afi'] = 'l2vpn'
                    new_entry['safi'] = 'evpn'
                else:
                    if ' ' in afi:
                        newafi, newsafi = afi.split()
                        new_entry['afi'] = newafi.lower().strip()
                        new_entry['safi'] = newsafi.lower().strip()
                    elif afi.startswith('ipv4'):
                        if 'Vpn' in afi:
                            new_entry['afi'] = 'vpnv4'
                            new_entry['safi'] = 'unicast'
                        else:
                            new_entry['afi'] = 'ipv4'
                            new_entry['safi'] = afi.split('ipv6')[1].lower()
                    elif afi.startswith('ipv6'):
                        if 'Vpn' in afi:
                            new_entry['afi'] = 'vpnv6'
                            new_entry['safi'] = 'unicast'
                        else:
                            new_entry['afi'] = 'ipv6'
                            new_entry['safi'] = afi.split('ipv6')[1].lower()

                subent = entry['_afiInfo'][afi]
                comm = subent.get('commAttriSentToNbr', '')
                if comm == 'extendedAndStandard':
                    new_entry['communityTypes'] = ['standard', 'extended']
                elif comm == 'standard':
                    new_entry['communityTypes'] = ['standard']

                new_entry['rrclient'] = 'routeReflectorClient' in subent
                new_entry['pfxRx'] = subent.get('acceptedPrefixCounter', 0)
                new_entry['pfxTx'] = subent.get('sentPrefixCounter', 0)
                new_entry['ingressRmap'] = \
                    subent.get('routeMapForIncomingAdvertisements', '')
                new_entry['egressRmap'] = \
                    subent.get('routeMapForOutgoingAdvertisements', '')
                new_entry['defOriginate'] = 'defaultSent' in subent
                new_entry['advertiseAllVni'] = 'advertiseAllVnis' in subent
                new_entry['nhUnchanged'] = \
                    'unchangedNextHopPropogatedToNbr' in subent

                new_entries.append(new_entry)

            drop_indices.append(i)

        processed_data += new_entries
        processed_data = np.delete(processed_data, drop_indices).tolist()

        return processed_data

    def _clean_linux_data(self, processed_data, raw_data):

        return self._clean_cumulus_data(processed_data, raw_data)
