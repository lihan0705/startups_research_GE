import random
import time
from itertools import zip_longest
from pprint import pprint

import pandas as pd
import requests
from fake_useragent import UserAgent

ua = UserAgent(os="windows", platforms="pc")

headers = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "content-type": "application/json",
    "origin": "https://startup-map.berlin",
    "priority": "u=1, i",
    "referer": "https://startup-map.berlin/",
    "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    "x-dealroom-app-id": "110618058",
    "x-requested-with": "XMLHttpRequest",
}

json_data = {
    "limit": 25,
    "offset": 0,
    "form_data": {
        "must": {
            "filters": {
                "regions": {
                    "values": [
                        "Berlin/Brandenburg Metropolitan Region",
                    ],
                    "execution": "or",
                },
                "years": {
                    "values": [
                        "2023",
                        "2024"
                    ],
                    "execution": "or",
                },
                "slug_locations": {
                    "values": [
                        "germany",
                    ],
                    "execution": "or",
                },
            },
            "execution": "and",
        },
        "should": {
            "filters": {},
        },
        "must_not": {
            "growth_stages": [
                "mature",
            ],
            "rounds": [
                "GRANT",
                "SPAC PRIVATE PLACEMENT",
            ],
            "tags": [
                "outside tech",
            ],
        },
    },
    "multi_match": False,
    "keyword_match_type": "fuzzy",
    "sort": "-date",
    "keyword_type": "default_next",
}

response = requests.post(
    "https://api.dealroom.co/api/v2/rounds", headers=headers, json=json_data
)


def request():
    while json_data["offset"] <= 800:
        offset = json_data["offset"]
        headers["user-agent"] = ua.random
        response = requests.post(
            "https://api.dealroom.co/api/v2/rounds", headers=headers, json=json_data
        )

        if response.status_code != 200:
            print(offset + 25)
            return

        yield response.json()
        time.sleep(random.uniform(0.6, 2.4))
        json_data["offset"] = offset + 25


table = []
title = [
    "name",
    "tagline",
    "investors_name",
    "address",
    "industries",
    "valuation",
    "last_round",
    "date",
]

i = 1
for data in request():
    items = data["items"]
    for item in items[1:]:
        name = item["company"]["name"]
        tagline = item["company"]["tagline"]

        # print(name)

        investors_name = ""
        if investors := item["investors"]:
            investors_name = investors[0]["name"]

        # if name == "Midas":
        #     pprint(item["company"]["hq_locations"])

        city = country = ""
        for location in item["company"]["hq_locations"]:
            if (not city) and location["city"]:
                city = location["city"]["name"]

            if (not country) and location["country"]:
                country = location["country"]["name"]

        address = f"{city}, {country}"

        industries = ""
        company_industries = item["company"]["industries"]
        sub_industries = item["company"]["sub_industries"]

        if company_industries and sub_industries:
            industries_name = company_industries[0]["name"]
            sub_industries_name = sub_industries[0]["name"]
            industries = f"{industries_name}\n{sub_industries_name}"

        elif company_industries:
            industries_name = company_industries[0]["name"]
            industries = industries_name

        year = item["year"]
        month = item["month"]
        date = f"{year}-{month}"

        valuation = ""
        if latest_valuation := item["company"]["latest_valuation"]:
            valuation_value = latest_valuation["valuation"]
            valuation_max = item["company"]["latest_valuation"]["valuation_max"]
            valuation_min = item["company"]["latest_valuation"]["valuation_min"]

            if valuation_value:
                valuation = f"€{round(valuation_value/1000000)}m"

            elif valuation_max and valuation_min:
                valuation = (
                    f"€{round(valuation_min/1000000)}-{round(valuation_max/1000000)}m"
                )

            else:
                valuation = ""

        amount = item["amount"]
        round_name = item["round"]
        last_round = f"€{amount}m{round_name}"

        row = [
            name,
            tagline,
            investors_name,
            address,
            industries,
            valuation,
            last_round,
            date,
        ]

        combined_dict = dict(zip_longest(title, row, fillvalue="default_value"))

        # pprint(combined_dict)
        table.append(combined_dict)
    pprint(f"第{i*25}行数据已处理完毕")
    i += 1

pd.DataFrame(table).to_csv("GE_startup_2023-2024.csv", index=False, columns=title)
