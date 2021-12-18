import copy
import datetime
import json
from pathlib import Path
from pprint import pprint
from textwrap import indent

import dateutil.parser
import packaging.version
import urllib3
from hammock import Hammock as hammock

urllib3.disable_warnings()

pmv = json.loads(hammock("https://gdmf.apple.com/v2/pmv").GET(verify=False).text)

by_os = {"iOS": [], "iPadOS": [], "macOS": [], "tvOS": []}
sorted_assets = {"iOS": {}, "iPadOS": {}, "macOS": {}, "tvOS": {}}

for asset_set in pmv:
    if asset_set == "PublicAssetSets":
        continue
    for asset_type in pmv[asset_set]:
        asset: dict
        for asset in pmv[asset_set][asset_type]:
            if any("iPhone" in i for i in asset["SupportedDevices"]):
                by_os["iOS"].append(asset)
            if any("iPad" in i for i in asset["SupportedDevices"]):
                by_os["iPadOS"].append(asset)
            # if any("Watch" in i for i in asset["SupportedDevices"]):
            #     by_os["watchOS"].append(asset)
            if any("AppleTV" in i for i in asset["SupportedDevices"]):
                by_os["tvOS"].append(asset)
            # if any("Audio" in i for i in asset["SupportedDevices"]):
            #     by_os["audioOS"].append(asset)
            if asset_type == "macOS":
                by_os["macOS"].append(asset)

json.dump(by_os, Path("by_os.json").open("w"), sort_keys=True, indent=4)

for os in by_os:
    for asset in by_os[os]:
        sorted_assets[os].setdefault(packaging.version.parse(asset["ProductVersion"]).major, []).append(asset)
for os in sorted_assets:
    for version in sorted_assets[os]:
        sorted_assets[os][version].sort(key=lambda x: dateutil.parser.parse(x["PostingDate"]), reverse=True)

pprint(sorted_assets, depth=2)

results = {i: {v: {} for v in sorted_assets[i]} for i in sorted_assets}

for os in sorted_assets:
    for version in sorted_assets[os]:
        for build in set([i["ProductVersion"] for i in sorted_assets[os][version]]):
            if [i["ProductVersion"] for i in sorted_assets[os][version]].count(build) > 1:
                print(f"{os} {version} {build}")

for os in sorted_assets:
    for version in sorted_assets[os]:
        for i, asset in enumerate(sorted_assets[os][version]):
            if i == 0:
                results[os][version][asset["ProductVersion"]] = {"Latest available": None}
            else:
                expiry = (datetime.datetime.replace(dateutil.parser.parse(sorted_assets[os][version][i - 1]["PostingDate"]), tzinfo=datetime.timezone.utc) + datetime.timedelta(days=90)).isoformat()
                results[os][version][asset["ProductVersion"]] = {expiry: None}
                
for os in results:
    for version in results[os]:
        keys = list(results[os][version].keys())
        for i, build in enumerate(keys):
            if i == 0:
                continue
            else:
                expiry = list(results[os][version][build].keys())[0]
                if i == len(keys) - 1:
                    results[os][version][build][expiry] = 90
                else:
                    before_expiry = datetime.datetime.replace(dateutil.parser.parse(list(results[os][version][sorted_assets[os][version][i + 1]["ProductVersion"]].keys())[0]), tzinfo=datetime.timezone.utc)
                    current = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                    results[os][version][build][expiry] = 90 - ((before_expiry - current).days)

json.dump(results, Path("deploy/results.json").open("w"), indent=4)
