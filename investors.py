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
    "fields": "uuid,path,type,name,is_serial_founder,is_founder,tagline,images(74x74),companies,deal_size_enhanced,emea_combined_prominence_unique,emea_seed_prominence_unique,emea_seriesa_prominence_unique,entity_sub_types,fundings,global_combined_prominence_unique,global_seed_prominence_growth,global_seed_prominence_unique,global_seriesa_prominence_unique,hq_locations,uuid,images(74x74),investment_stages,investments,investments_num,investments_valuation_enhanced,investor_exit_score,investor_exits_funding_enhanced,investor_exits_num,investor_fundings_3_months_enhanced,investor_fundings_6_months_enhanced,investor_fundings_12_months_enhanced,investor_fundings_24_months_enhanced,investor_total,investor_total_funding_enhanced,investor_total_rank,is_editorial,is_serial_founder,is_founder,lp_investments,name,notable_investments,path,preferred_round,rounds_count_3_months,rounds_count_6_months,rounds_count_12_months,rounds_count_24_months,rounds_experience,tagline,top_investments_num,type,company_status,investor_rounds_by_params(emea_combined_prominence_unique)",
    "limit": 25,
    "offset": 0,
    "form_data": {
        "must": {
            "filters": {
                "all_regions": {
                    "values": [
                        "Berlin/Brandenburg Metropolitan Region",
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
        "must_not": {},
    },
    "multi_match": False,
    "keyword_match_type": "fuzzy",
    "sort": "emea_combined_prominence_unique",
    "keyword_type": "default_next",
}


def request():
    # json_data["offset"] = 600
    while json_data["offset"] <= 1330:
        offset = json_data["offset"]
        headers["user-agent"] = ua.random
        response = requests.post(
            "https://api.dealroom.co/api/v2/investors",
            headers=headers,
            json=json_data,
            timeout=None,
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
    "emea_combined_prominence_unique",
    "preferred_round",
    "address",
    "deal_size_range",
    "fundings_total",
    "participated_in_deals_totaling",
    "investments_total",
    "total_value_of_current_portfolio",
    "notable_investments",
    "investor_exits_num",
    "investor_exit_score",
    "total_value_of_exits",
]

i = 1
for data in request():
    items = data["items"]
    for item in items:
        name = item["name"]
        tagline = item["tagline"]

        emea_combined_prominence_unique = item["emea_combined_prominence_unique"]
        preferred_round = item["preferred_round"]

        city = country = ""
        for location in item["hq_locations"]:
            if (not city) and location["city"]:
                city = location["city"]["name"]

            if (not country) and location["country"]:
                country = location["country"]["name"]

        address = f"{city}, {country}"

        max = item["deal_size_enhanced"]["max"]
        min = item["deal_size_enhanced"]["min"]

        if max and min:
            deal_size_range = f"${int(min/1000)}k-${5000000/1000000:.1f}m"
        else:
            deal_size_range = ""

        fundings_total = item["fundings"]["total"]

        investor_total_funding_enhanced_amount = item[
            "investor_total_funding_enhanced"
        ]["amount"]

        participated_in_deals_totaling = (
            f"€{investor_total_funding_enhanced_amount/1000000000:.1f}b"
        )

        investments_total = item["investments"]["total"]

        investments_valuation_enhanced_amount = item["investments_valuation_enhanced"][
            "amount"
        ]
        total_value_of_current_portfolio = (
            f"€{investments_valuation_enhanced_amount/1000000000:.1f}b"
        )

        notable_investments = ",".join(
            [item["name"] for item in item["notable_investments"]["items"]]
        )

        investor_exits_num = item["investor_exits_num"]
        investor_exit_score = item["investor_exit_score"]

        investor_exits_funding_enhanced_amount = item[
            "investor_exits_funding_enhanced"
        ]["amount"]
        total_value_of_exits = (
            f"€{investor_exits_funding_enhanced_amount/1000000000:.1f}b"
        )

        row = [
            name,
            tagline,
            emea_combined_prominence_unique,
            preferred_round,
            address,
            deal_size_range,
            fundings_total,
            participated_in_deals_totaling,
            investments_total,
            total_value_of_current_portfolio,
            notable_investments,
            investor_exits_num,
            investor_exit_score,
            total_value_of_exits,
        ]

        combined_dict = dict(zip_longest(title, row, fillvalue="default_value"))

        # pprint(combined_dict)
        table.append(combined_dict)

    pprint(f"第{i*25}行数据已处理完毕")
    i += 1

pd.DataFrame(table).to_excel(
    "investors.xlsx", engine="xlsxwriter", index=False, columns=title
)
