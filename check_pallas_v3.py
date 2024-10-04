import base64
import datetime
import io
import itertools
import json
import plistlib
import zipfile
from pathlib import Path
from pprint import pprint

import packaging.version
import requests
import urllib3

urllib3.disable_warnings()

session = requests.Session()
session.verify = False

# TODO: Work on expiry

documentation_cache = {}

asset_audiences = {
    "iOS": {
        "iOS release": "01c1d682-6e8f-4908-b724-5501fe3f5e5c",
        "iOS internal": "ce9c2203-903b-4fb3-9f03-040dc2202694",
        "iOS security updates": "c724cb61-e974-42d3-a911-ffd4dce11eda",
        "iOS 11 developer beta": "b7580fda-59d3-43ae-9488-a81b825e3c73",
        "iOS 11 AppleSeed beta": "f23050eb-bdfa-4b23-9eca-453e3b1a247c",
        "iOS 11 public beta": "5839f7cf-9610-483a-980f-6c4266a22f17",
        "iOS 12 developer beta": "ef473147-b8e7-4004-988e-0ae20e2532ef",
        "iOS 12 public beta": "94bf0742-38e6-4379-adf9-ec9995dde586",
        "iOS 13 developer beta": "d8ab8a45-ee39-4229-891e-9d3ca78a87ca",
        "iOS 13 public beta": "98bcaac1-66ed-4691-80e4-739f8ed5bb19",
        "iOS 14 developer beta": "dbbb0481-d521-4cdf-a2a4-5358affc224b",
        "iOS 14 AppleSeed beta": "84da8706-e267-4554-8207-865ae0c3a120",
        "iOS 14 public beta": "1506c359-28af-4ee1-a043-42df9d496d38",
        "iOS 15 developer beta": "ce48f60c-f590-4157-a96f-41179ca08278",
        "iOS 15 public beta": "9e12a7a5-36ac-4583-b4fb-484736c739a8",
        "iOS 16 developer beta": "a6050bca-50d8-4e45-adc2-f7333396a42c",
        "iOS 16 AppleSeed beta": "817ce601-f365-4294-8982-b00f547bbe4a",
        "iOS 16 public beta": "7466521f-cc37-4267-8f46-78033fa700c2",
    },
    "tvOS": {
        "tvOS release": "356d9da0-eee4-4c6c-bbe5-99b60eadddf0",
        "tvOS 11 developer beta": "ebd90ea1-6216-4a7c-920e-666faccb2d50",
        "tvOS 12 developer beta": "5b220c65-fe50-460b-bac5-b6774b2ff475",
        "tvOS 13 developer beta": "975af5cb-019b-42db-9543-20327280f1b2",
        "tvOS 13 AppleSeed beta": "B79E95A7-1E51-4A6D-94F8-2BC2F9DBB000",
        "tvOS 14 developer beta": "65254ac3-f331-4c19-8559-cbe22f5bc1a6",
        "tvOS 14 AppleSeed beta": "a46c2f97-0afb-4a36-bcf6-8c0d74ec21be",
        "tvOS 15 developer beta": "4d0dcdf7-12f2-4ebf-9672-ac4a4459a8bc",
        "tvOS 15 AppleSeed beta": "3565d2d0-06b5-450d-9c01-7086cdd13f97",
        "tvOS 16 developer beta": "d6bac98b-9e2a-4f87-9aba-22c898b25d84",
    },
    "watchOS": {
        "watchOS release": "b82fcf9c-c284-41c9-8eb2-e69bf5a5269f",
        "watchOS 4 developer beta": "f659e06d-86a2-4bab-bcbb-61b7c60969ce",
        "watchOS 5 developer beta": "e841259b-ad2e-4046-b80f-ca96bc2e17f3",
        "watchOS 6 developer beta": "d08cfd47-4a4a-4825-91b5-3353dfff194f",
        "watchOS 7 developer beta": "ff6df985-3cbe-4d54-ba5f-50d02428d2a3",
        "watchOS 7 public beta": "6ac47c79-d0c4-42dc-b499-baa45e363c40",
        "watchOS 8 developer beta": "b407c130-d8af-42fc-ad7a-171efea5a3d0",
        "watchOS 8 public beta": "f755ea49-3d47-4829-9cdf-87aa76456282",
        "watchOS 9 developer beta": "341f2a17-0024-46cd-968d-b4444ec3699f",
        "watchOS 9 public beta": "4935cf61-2a58-437a-be3f-4db423970e43",
    },
    "audioOS": {
        "audioOS release": "0322d49d-d558-4ddf-bdff-c0443d0e6fac",
        "audioOS 14 AppleSeed beta": "b05ddb59-b26d-4c89-9d09-5fda15e99207",
        "audioOS 15 AppleSeed beta": "58ff8d56-1d77-4473-ba88-ee1690475e40",
        "audioOS 16 AppleSeed beta": "59377047-7b3f-45b9-8e99-294c0daf3c85",
    },
    "macOS": {
        "macOS release": "60b55e25-a8ed-4f45-826c-c1495a4ccc65",
        "macOS 11 developer beta": "ca60afc6-5954-46fd-8cb9-60dde6ac39fd",
        "macOS 11 AppleSeed beta": "215447a0-bb03-4e18-8598-7b6b6e7d34fd",
        "macOS 11 public beta": "902eb66c-8e37-451f-b0f2-ffb3e878560b",
        "macOS 12 developer beta": "298e518d-b45e-4d36-94be-34a63d6777ec",
        "macOS 12 AppleSeed beta": "a3799e8a-246d-4dee-b418-76b4519a15a2",
        "macOS 12 public beta": "9f86c787-7c59-45a7-a79a-9c164b00f866",
        "macOS 13 developer beta": "683e9586-8a82-4e5f-b0e7-767541864b8b",
        "macOS 13 AppleSeed beta": "3c45c074-41be-4b5b-a511-8592336e6783",
        "macOS 13 public beta": "800034a9-994c-4ecc-af4d-7b3b2ee0a5a6",
    },
}

alternate_names = {"c724cb61-e974-42d3-a911-ffd4dce11eda": "iOS 14 Alternate Updates"}


oses = {
    # "iOS (iPhone 14 series)": {
    #     "main": asset_audiences["iOS"]["iOS release"],
    #     "os_category": "iOS",
    #     "default_name": "iPhone",
    #     "devices": {
    #         "iPhone 14": {
    #             "ProductType": "iPhone14,7",
    #             "HWModelStr": "D27AP",
    #         },
    #     },
    # },
    # "iPhone 12 series/13 series": {
    #     "main": asset_audiences["iOS"]["iOS release"],
    #     "os_category": "iOS",
    #     "default_name": "iPhone",
    #     "devices": {
    #         "iPhone 12": {
    #             "ProductType": "iPhone13,2",
    #             "HWModelStr": "D53gAP",
    #         },
    #     },
    # },
    "September 2024 iPhones": {
        "main": asset_audiences["iOS"]["iOS release"],
        "os_category": "iOS",
        "default_name": "iPhone",
        "devices": {
            "iPhone 16": {
                "ProductType": "iPhone17,3",
                "HWModelStr": "D47AP",
            },
        },
    },
    "iOS (devices supporting iOS 18)": {
        "main": asset_audiences["iOS"]["iOS release"],
        "os_category": "iOS",
        "default_name": "iPhone",
        "devices": {
            "iPhone 14": {
                "ProductType": "iPhone14,7",
                "HWModelStr": "D27AP",
            },
            # "iPhone X": {
            #   "ProductType": "iPhone10,6",
            #   "HWModelStr": "D221AP",
            # },
            # "iPhone XR": {
            #     "ProductType": "iPhone11,8",
            #     "HWModelStr": "N841AP",
            # },
            # "iPhone 12": {
            #     "ProductType": "iPhone13,2",
            #     "HWModelStr": "D53gAP",
            # },
            # "iPhone 6s": {
            #     "ProductType": "iPhone8,1",
            #     "HWModelStr": "N71AP",
            # },
            # "iPhone 7": {"ProductType": "iPhone9,3", "HWModelStr": "D101AP"},
            # "iPhone 7 v2": {"ProductType": "iPhone9,1", "HWModelStr": "D10AP"},
        },
    },
    "iOS Legacy v3 (devices supporting up to iOS 16)": {
        "main": asset_audiences["iOS"]["iOS release"],
        "os_category": "iOS",
        "default_name": "iPhone",
        "devices": {
            "iPhone X": {
                "ProductType": "iPhone10,6",
                "HWModelStr": "D221AP",
            },
        },
    },
    "iOS Legacy v2 (device supporting up to iOS 15)": {
        "main": asset_audiences["iOS"]["iOS release"],
        "os_category": "iOS",
        "default_name": "iPhone",
        "devices": {
            "iPhone 6s": {
                "ProductType": "iPhone8,1",
                "HWModelStr": "N71AP",
            },
            # "iPhone 7": {"ProductType": "iPhone9,3", "HWModelStr": "D101AP"},
            # "iPhone 7 v2": {"ProductType": "iPhone9,1", "HWModelStr": "D10AP"},
        },
    },
    "iOS Legacy (device supporting up to iOS 12)": {
        "main": asset_audiences["iOS"]["iOS release"],
        "os_category": "iOS",
        "default_name": "iPhone",
        "devices": {
            "iPhone 6+": {
                "ProductType": "iPhone7,1",
                "HWModelStr": "N56AP",
            }
        },
    },
    "M4 iPads": {
        "main": asset_audiences["iOS"]["iOS release"],
        "default_name": "iPad",
        "os_category": "iPadOS",
        "devices": {
            "iPad Pro 11-inch (M4) Wi-Fi": {
                "ProductType": "iPad16,3",
                "HWModelStr": "J717AP",
            },
            # "iPad (8th gen) WiFi": {
            #     "ProductType": "iPad11,6",
            #     "HWModelStr": "J171aAP",
            # },
        },
    },
    "iPadOS (devices supporting iPadOS 18)": {
        "main": asset_audiences["iOS"]["iOS release"],
        "default_name": "iPad",
        "os_category": "iPadOS",
        "devices": {
            "iPad Pro 12.9-inch (6th generation) WiFi": {
                "ProductType": "iPad14,5",
                "HWModelStr": "J620AP",
            },
            # "iPad (8th gen) WiFi": {
            #     "ProductType": "iPad11,6",
            #     "HWModelStr": "J171aAP",
            # },
        },
    },
    "iPadOS Legacy v4 (devices supporting up to iPadOS 17)": {
        "main": asset_audiences["iOS"]["iOS release"],
        "default_name": "iPad",
        "os_category": "iPadOS",
        "devices": {
            "iPad (6th generation) Wi-Fi": {
                "ProductType": "iPad7,5",
                "HWModelStr": "J71bAP",
            },
        },
    },
    "iPadOS Legacy v3 (devices supporting up to iPadOS 16)": {
        "main": asset_audiences["iOS"]["iOS release"],
        "default_name": "iPad",
        "os_category": "iPadOS",
        "devices": {
            "iPad (5th generation) Wi-Fi": {
                "ProductType": "iPad6,11",
                "HWModelStr": "J71sAP",
            },
        },
    },
    "iPadOS Legacy v2 (devices supporting up to iPadOS 15)": {
        "main": asset_audiences["iOS"]["iOS release"],
        "default_name": "iPad",
        "os_category": "iPadOS",
        "devices": {
            "iPad mini 4": {
                "ProductType": "iPad5,1",
                "HWModelStr": "J96AP",
            },
        },
    },
    "iPadOS Legacy (devices supporting up to iOS 12)": {
        "main": asset_audiences["iOS"]["iOS release"],
        "default_name": "iPad",
        "os_category": "iPadOS",
        "devices": {
            "iPad mini 3": {
                "ProductType": "iPad4,9",
                "HWModelStr": "J87mAP",
            },
        },
    },
    "tvOS": {
        "main": "356d9da0-eee4-4c6c-bbe5-99b60eadddf0",
        "default_name": "TV",
        "os_category": "tvOS",
        "devices": {
            # "Apple TV HD": {"ProductType": "AppleTV5,3", "HWModelStr": "J42dAP"},
            "AppleTV11,1": {"ProductType": "AppleTV11,1", "HWModelStr": "J305AP"},
        },
    },
    # "watchOS": {
    #     "main": "b82fcf9c-c284-41c9-8eb2-e69bf5a5269f",
    #     "devices": {
    #         "Watch5,10": {"ProductType": "Watch5,10", "HWModelStr": "N140bAP"},
    #         "Watch4,2": {"ProductType": "Watch4,2", "HWModelStr": "N131bAP"},
    #         "Watch6,2": {"ProductType": "Watch6,2", "HWModelStr": "N157bAP"},
    #     },
    # },
    # "audioOS": {
    #     "main": "0322d49d-d558-4ddf-bdff-c0443d0e6fac",
    #     "devices": {
    #         "AudioAccessory1,2": {"ProductType": "AudioAccessory1,2", "HWModelStr": "B238AP"},
    #     },
    # },
    "macOS": {
        "type": "com.apple.MobileAsset.MacSoftwareUpdate",
        "main": "60b55e25-a8ed-4f45-826c-c1495a4ccc65",
        "default_name": "Mac",
        "os_category": "macOS",
        "devices": {
            "MacPro7,1": {"HWModelStr": "J160AP", "ProductType": "MacPro7,1"},  # MacPro7,1,
        },
    },
}


REQUEST_DICT = {
    # "AssetAudience": "",
    # "CertIssuanceDay": "2019-09-06", # Not needed
    "ClientVersion": 2,
    "CompatibilityVersion": 20,
    "AssetType": "com.apple.MobileAsset.SoftwareUpdate",
    "Supervised": True,
    "ProductVersion": "0",
    "BuildVersion": "0",
}

ASSETS_URL = "https://gdmf.apple.com/v2/assets"


def get_json(content):
    content = content.split(".")[1]
    content += "=" * (len(content) % 4)
    return json.loads(base64.b64decode(content))


pmv = json.loads(session.get("https://gdmf.apple.com/v2/pmv").text)

by_os = {"iOS": [], "iPadOS": [], "macOS": [], "tvOS": []}
for asset_type in pmv["AssetSets"]:
    asset: dict
    for asset in pmv["AssetSets"][asset_type]:
        if any("iPhone" in i for i in asset["SupportedDevices"]):
            by_os["iOS"].append(asset)
        if any("iPad" in i for i in asset["SupportedDevices"]):
            by_os["iPadOS"].append(asset)
        if any("AppleTV" in i for i in asset["SupportedDevices"]):
            by_os["tvOS"].append(asset)
        if asset_type == "macOS":
            by_os["macOS"].append(asset)

json.dump(by_os, Path("by_os.json").open("w"), sort_keys=True, indent=4)


def major(version):
    return packaging.version.parse(version).major  # type: ignore


# All we really get out of pmv is the list of versions to try to RPV.
# We cannot rely on each version being unique (thx Apple), so we cannot really use any other data.


pmv_versions = by_os.copy()
for os in by_os:
    product_versions = []
    for asset in by_os[os]:
        if asset["ProductVersion"] not in product_versions:
            product_versions.append(asset["ProductVersion"])
    pmv_versions[os] = product_versions

json.dump(pmv_versions, Path("pmv_versions.json").open("w"), sort_keys=True, indent=4)

sorted_assets = {i: {"default": [], "alternate": []} for i in oses}


def check_in_assets(os, build, date, alternate=False):
    for i in itertools.chain.from_iterable(sorted_assets[os].values()):
        if i["build"] == build and i["alternate"] == alternate:  # and i["pmv_posting"] == date:
            return i
    return None


def get_title(default_name, request):
    try:
        if asset["SUDocumentationID"] not in documentation_cache.setdefault(default_name, {}):
            docs_dict = request.copy()
            docs_dict["AssetType"] = "com.apple.MobileAsset.SoftwareUpdateDocumentation"
            docs_dict["SUDocumentationID"] = asset["SUDocumentationID"]

            docs_response = session.post(ASSETS_URL, json=docs_dict)
            docs_response.raise_for_status()
            docs_result = get_json(docs_response.text)
            documentation_cache[default_name][asset["SUDocumentationID"]] = None
            if docs_result["Assets"]:
                docs_zip = zipfile.ZipFile(
                    io.BytesIO(session.get(docs_result["Assets"][0]["__BaseURL"] + docs_result["Assets"][0]["__RelativePath"]).content)
                )
                if "AssetData/en.lproj/documentation.strings" in docs_zip.namelist():
                    documentation_cache[default_name][asset["SUDocumentationID"]] = plistlib.loads(
                        docs_zip.read("AssetData/en.lproj/documentation.strings")
                    ).get("HumanReadableUpdateName")
    except requests.HTTPError:
        documentation_cache[default_name][asset["SUDocumentationID"]] = None

    return documentation_cache[default_name][asset["SUDocumentationID"]]


# Get the basic info
# TODO: Can you RPV with alternate SU?
for os, this_os in oses.items():
    for device in this_os["devices"]:
        for available_version in pmv_versions[this_os["os_category"]]:
            print(f"Checking {available_version} with {device}")

            request_dict = REQUEST_DICT.copy()
            request_dict.update(this_os["devices"][device])
            request_dict["AssetAudience"] = this_os["main"]
            if this_os.get("type"):
                request_dict["AssetType"] = this_os["type"]
            if "DeviceName" not in request_dict:
                request_dict["DeviceName"] = this_os["default_name"]
            request_dict["DelayRequested"] = False
            request_dict["RequestedProductVersion"] = available_version

            try:
                response = session.post(ASSETS_URL, json=request_dict)
                response.raise_for_status()
                result = get_json(response.text)

                if result["Assets"]:
                    for asset in result["Assets"]:
                        version = asset["OSVersion"].replace("9.9.", "")
                        build = asset["Build"]
                        posting = result["PostingDate"]

                        if asset.get("ReleaseType") == "Beta" and os == "tvOS":
                            continue

                        unit = check_in_assets(os, build, posting)
                        if not unit:
                            unit = {
                                "title": None,
                                "name": version,
                                "build": build,
                                "alternate": False,
                                "days": [],
                                "theoretical_date": None,
                                "theoretical": None,
                                "mdm_available": True,
                                "pmv_posting": posting,
                            }
                            sorted_assets[os]["default"].append(unit)

                        if not unit["title"]:
                            unit["title"] = get_title(this_os["default_name"], request_dict)

                        print(f"Found {version} with device {device}")
                else:
                    # minor_versions[minor_version]["mdm_available"] = False
                    print(f"No assets found for {available_version} with {device}")
            except requests.HTTPError:
                # minor_versions[minor_version]["mdm_available"] = False
                print(f"Requested product version {available_version} with {device} not available")
        json.dump(
            sorted_assets,
            Path("testing.json").open("w"),
            indent=4,
            default=lambda x: x.isoformat() if isinstance(x, datetime.datetime) else x,
        )


# Get the actual periods
for os, this_os in oses.items():
    for device in this_os["devices"]:
        for period in range(91):
            print(f"Checking {period} with {device}")

            request_dict = REQUEST_DICT.copy()
            request_dict.update(this_os["devices"][device])
            request_dict["AssetAudience"] = this_os["main"]
            if this_os.get("type"):
                request_dict["AssetType"] = this_os["type"]
            if "DeviceName" not in request_dict:
                request_dict["DeviceName"] = this_os["default_name"]
            if period:
                request_dict["DelayRequested"] = True
                request_dict["DelayPeriod"] = period
            else:
                request_dict["DelayRequested"] = False

            response = session.post(ASSETS_URL, json=request_dict)
            response.raise_for_status()
            result = get_json(response.text)

            if result["Assets"]:
                for asset in result["Assets"]:
                    version = asset["OSVersion"].replace("9.9.", "")
                    build = asset["Build"]
                    posting = result["PostingDate"]

                    if asset.get("ReleaseType") == "Beta" and os == "tvOS":
                        continue

                    unit = check_in_assets(os, build, posting)
                    if not unit:
                        unit = {
                            "title": None,
                            "name": version,
                            "build": build,
                            "alternate": False,
                            "days": [period],
                            "theoretical_date": None,
                            "theoretical": None,
                            "mdm_available": False,
                            "pmv_posting": posting,
                        }
                        sorted_assets[os]["default"].append(unit)

                    if period not in unit["days"]:
                        unit["days"].append(period)

                    if not unit["title"]:
                        unit["title"] = get_title(this_os["default_name"], request_dict)
                    print(f"Found {version} for period {period} with device {device}")

                    if asset.get("EnableAlternateAssetAudience"):
                        alternate_audience = asset["AlternateAssetAudienceUUID"]
                        request_dict["AssetAudience"] = alternate_audience
                        response = session.post(ASSETS_URL, json=request_dict)
                        response.raise_for_status()
                        result = get_json(response.text)

                        if result["Assets"]:
                            for asset in result["Assets"]:
                                version = asset["OSVersion"].replace("9.9.", "")
                                build = asset["Build"]
                                posting = result["PostingDate"]

                                if asset.get("ReleaseType") == "Beta" and os == "tvOS":
                                    continue

                                unit = check_in_assets(os, build, posting, True)
                                if not unit:
                                    unit = {
                                        "title": None,
                                        "name": version,
                                        "build": build,
                                        "alternate": True,
                                        "days": [period],
                                        "theoretical_date": None,
                                        "theoretical": None,
                                        "mdm_available": False,
                                        "pmv_posting": posting,
                                    }
                                    sorted_assets[os]["alternate"].append(unit)

                                if period not in unit["days"]:
                                    unit["days"].append(period)

                                if not unit["title"]:
                                    unit["title"] = get_title(this_os["default_name"], request_dict)

                                print(f"Found alternate {version} for period {period} with device {device}")
                        else:
                            print(f"No alternate assets found for {period} with {device}")
            else:
                print(f"No assets found for {device}")
        json.dump(
            sorted_assets,
            Path("testing.json").open("w"),
            indent=4,
            default=lambda x: x.isoformat() if isinstance(x, datetime.datetime) else x,
        )


class reversor:
    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, other):
        return other.obj == self.obj

    def __lt__(self, other):
        return other.obj < self.obj


for os in sorted_assets:
    sorted_assets[os]["default"].sort(key=lambda x: (x["days"][0] if x["days"] else 91, reversor(packaging.version.parse(x["name"]))))
    sorted_assets[os]["alternate"].sort(key=lambda x: (x["days"][0] if x["days"] else 91, reversor(packaging.version.parse(x["name"]))))

for os in sorted_assets:
    for path, versions in sorted_assets[os].items():
        for i, version in enumerate(versions):
            if 0 in version["days"]:
                version["theoretical_date"] = None
                version["theoretical"] = 0
                continue
            current = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            # version["theoretical_date"] = current + datetime.timedelta(days=(90 - versions[i - 1]["days"][-1]))
            if len(version["days"]):
                version["theoretical_date"] = current + datetime.timedelta(days=(90 - version["days"][0] + 1))
                version["theoretical"] = version["days"][-1] if len(version["days"]) else -1
            else:
                j = 1
                while not versions[i - j]["days"]:
                    j += 1

                version["theoretical_date"] = current + datetime.timedelta(days=(90 - versions[i - j]["days"][-1]))
                version["theoretical"] = -1
            # if i == 0:
            #     version["theoretical_date"] = None

json.dump(
    sorted_assets, Path("testing.json").open("w"), indent=4, default=lambda x: x.isoformat() if isinstance(x, datetime.datetime) else x
)

resorted_assets = {i: [] for i in oses}

for os in sorted_assets:
    resorted_assets[os] = list(itertools.chain.from_iterable(sorted_assets[os].values()))

json.dump(
    resorted_assets, Path("testing.json").open("w"), indent=4, default=lambda x: x.isoformat() if isinstance(x, datetime.datetime) else x
)

for os in sorted_assets:
    resorted_assets[os].sort(key=lambda x: (x["days"][0] if x["days"] else 91, reversor(packaging.version.parse(x["name"]))))
json.dump(
    resorted_assets, Path("testing.json").open("w"), indent=4, default=lambda x: x.isoformat() if isinstance(x, datetime.datetime) else x
)

minified = {}

for os, versions in resorted_assets.items():
    for version in versions:
        current = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        minified.setdefault(os, []).append(
            {
                "name": f"{version['title'] or (oses[os]['os_category'] + ' ' + version['name'])} ({version['build']})",
                "alternate": version["alternate"],
                "date": version["theoretical_date"].isoformat() if version["theoretical_date"] else None,
                "delay": version["theoretical"],  # 0 = latest, -1 - imminent removal, other - usable delay
                "latest": version["theoretical"] == 0,
                "imminent": version["theoretical"] == -1,
                "mdm_available": version["mdm_available"],
                "mdm_only": not version["days"],
            }
        )


for os, versions in minified.items():
    for version in list(versions):
        if version["mdm_only"] and not version["mdm_available"]:  # Dead
            versions.remove(version)

minified["_date"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

json.dump(minified, Path("deploy/minified-v3.json").open("w"), indent=4)
