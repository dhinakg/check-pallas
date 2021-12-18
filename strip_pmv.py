import json
from pathlib import Path

pmv = json.load(Path("pmv.json").open())

for asset_set in pmv:
    for type in pmv[asset_set]:
        asset: dict
        for asset in list(pmv[asset_set][type]):
            if not any("iPhone" in i for i in asset["SupportedDevices"]):
                pmv[asset_set][type].remove(asset)
            else:
                asset.pop("SupportedDevices")

json.dump(pmv, Path("pmv_clean.json").open("w"), sort_keys=True, indent=4)