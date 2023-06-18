#!/usr/bin/env python3

import ipaddress
import json
import urllib.parse
import urllib.request

IXLAN = 13  # Seattle Internet Exchange (MTU 1500)
PEERS = [
    42,  # PCH
    174,  # Cogent
    714,  # Apple
    3361,  # Digital Fortress
    3856,  # PCH
    6456,  # Altopia
    6939,  # Hurricane Electric
    8075,  # Microsoft
    8309,  # Sipartech
    11404,  # Wave
    16276,  # OVH
    16509,  # Amazon
    18106,  # ViewQwest
    19679,  # Dropbox
    19754,  # Fusion
    20940,  # Akamai
    25668,  # AEBC
    32212,  # Sky Fiber
    32934,  # Meta
    33108,  # SIX Route Servers
    36459,  # GitHub
    46489,  # Twitch
    46997,  # Nato Internet
    47065,  # PEERING Testbed
    62887,  # Whitesky
    63069,  # Sureline
    395823,  # doof.net
]
DENY_PEERS = [13335, 53340]


def fetch_networks(asns):
    asn_strs = ",".join(str(x) for x in asns)

    networks = {}
    with urllib.request.urlopen(
        "https://www.peeringdb.com/api/net?{}".format(
            urllib.parse.urlencode({"asn__in": asn_strs})
        )
    ) as f:
        for network in json.load(f)["data"]:
            data = {
                k: network[k]
                for k in ["name", "asn", "info_prefixes4", "info_prefixes6"]
                if k in network
            }

            if "AS{}".format(network["asn"]) in data["name"]:
                data["name"] = (
                    data["name"].replace("AS{}".format(network["asn"]), "").strip()
                )
            if data["name"].startswith("The "):
                data["name"] = data["name"][4:].strip()
            data["name"] = " {} ".format(data["name"]).replace(" - ", "").strip()

            networks[network["asn"]] = {
                "data": data,
                "neighbors": [],
            }

    with urllib.request.urlopen(
        "https://www.peeringdb.com/api/netixlan?{}".format(
            urllib.parse.urlencode({"ixlan": IXLAN, "asn__in": asn_strs})
        )
    ) as f:
        for ixlan in json.load(f)["data"]:
            networks[ixlan["asn"]]["neighbors"].extend(
                [ixlan["ipaddr4"], ixlan["ipaddr6"]]
            )

    return networks


def construct_network(network):
    group = ["remote-as {}".format(network["data"]["asn"])]
    for option in network.get("options", []):
        group.append(option)

    neighbors = sorted(
        (ipaddress.ip_address(x) for x in network["neighbors"]),
        key=ipaddress.get_mixed_type_key,
    )
    i = 0
    ipv6_yet = False

    for neighbor in neighbors:
        if not ipv6_yet and neighbor.version == 6:
            i = 0
            ipv6_yet = True

        descr = "v{}{}{}".format(
            neighbor.version,
            (
                " rs{} ".format(int(neighbor) % 256)
                if network["data"]["asn"] == 33108
                else " +!@#%"[i]
            ),
            escape(network["data"]["name"]),
        )[:31]
        neigh = [
            'descr "{}"'.format(descr),
            "announce IPv{} unicast".format(neighbor.version),
        ]

        if (
            prefixes := network["data"].get("info_prefixes{}".format(neighbor.version))
        ) is not None:
            neigh.append("max-prefix {} restart 15".format(prefixes))

        group.append({"neighbor {}".format(neighbor): neigh})
        i += 1

    return {'group "AS{}"'.format(network["data"]["asn"]): group}


def escape(s):
    return s.replace('"', "")


def serialize(x):
    def indent(s):
        return "".join("\t" + line for line in s.splitlines(True))

    data = []
    for item in x:
        if isinstance(item, dict):
            for k, v in item.items():
                data.append("{} {{\n{}\n}}".format(k, indent(serialize(v))))
        else:
            data.append(item)
    return "\n".join(data)


if __name__ == "__main__":
    networks = fetch_networks(PEERS)

    # SIX Route Servers -- prio 99
    networks[33108]["options"] = ["set localpref 99", "enforce neighbor-as no"]

    # Cogent -- not via SIX, prio 80, no max prefix
    networks[174]["neighbors"] = ["38.142.48.185", "2001:550:2:13::83:1"]
    networks[174]["options"] = ["set localpref 80"]
    del networks[174]["data"]["info_prefixes4"]
    del networks[174]["data"]["info_prefixes6"]

    # Digital Fortress -- does not currently peer via IPv6
    networks[3361]["neighbors"].remove("2001:504:16::d21")

    conf = [
        "### THIS FILE IS GENERATED",
        "### modify peeringdb.py in the config repo instead",
        "AS 64241",
        "listen on 206.81.81.87",
        "listen on 2001:504:16::faf1",
        "listen on 38.142.48.186",
        "listen on 2001:550:2:13::83:2",
        "network 209.251.245.0/24",
        "network 2620:fc:c000::/48",
        "router-id 206.81.81.87",
    ]
    conf.extend(map(construct_network, networks.values()))
    conf.append(
        {
            'match to group "AS33108" set': [
                " ".join(f"community 0:{asn}" for asn in DENY_PEERS)
            ]
        }
    )
    conf.extend(
        'deny quick from group "AS33108" peer-as {}'.format(asn) for asn in DENY_PEERS
    )

    print(serialize(conf))
