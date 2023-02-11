#!/usr/bin/env python3

import ipaddress
import json
import urllib.parse
import urllib.request

IXLAN = 13  # Seattle Internet Exchange (MTU 1500)
PEERS = [
    6456,  # Altopia
    42,  # PCH
    3856,  # PCH
    46489,  # Twitch
    19754,  # Fusion
    19679,  # Dropbox
    16276,  # OVH
    395823,  # doof.net
    8075,  # Microsoft
    16509,  # Amazon
    3361,  # Digital Fortress
    25668,  # AEBC
    36459,  # GitHub
    32934,  # Meta
    32212,  # Sky Fiber
    46997,  # Nato Internet
    20940,  # Akamai
    47065,  # PEERING Testbed
    18106,  # ViewQwest
    62887,  # Whitesky
    63069,  # Sureline
    714,  # Apple
    11404,  # Wave
]


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
                else [" ", "+", "!", "@"][i]
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
    networks = fetch_networks([6939, 33108, *PEERS])

    conf = [
        "### THIS FILE IS GENERATED",
        "### modify peeringdb.py in the config repo instead",
        "listen on 206.81.81.87",
        "listen on 2001:504:16::faf1",
        "listen on 38.142.48.186",
        "listen on 2001:550:2:13::83:2",
        "AS 64241",
        "router-id 206.81.81.87",
        "network 209.251.245.0/24",
        "network 2620:fc:c000::/48",
    ]

    # Hurricane Electric -- transit network, so don't set max-prefix
    as6939 = networks.pop(6939)
    as6939["options"] = ["set localpref 90", "set weight +5"]
    del as6939["data"]["info_prefixes4"]
    del as6939["data"]["info_prefixes6"]
    conf.append(construct_network(as6939))

    # Cogent -- transit network
    conf.append(
        construct_network(
            {
                "data": {
                    "name": "Cogent Communications, Inc.",
                    "asn": 174,
                },
                "options": ["set localpref 80", "set prepend-self 3"],
                "neighbors": ["38.142.48.185", "2001:550:2:13::83:1"],
            }
        )
    )

    # SIX route servers
    as33108 = networks.pop(33108)
    as33108["options"] = ["set localpref 99", "enforce neighbor-as no"]
    conf.append(construct_network(as33108))

    conf.extend(
        [
            'match to group "AS33108" set { community 0:13335 community 0:53340 }',
            'deny quick from group "AS33108" peer-as 13335',
            'deny quick from group "AS33108" peer-as 53340',
        ]
    )

    conf.extend(construct_network(networks[asn]) for asn in PEERS)
    print(serialize(conf))
