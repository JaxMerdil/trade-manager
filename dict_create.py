import json

with open("offers_ids.txt", "r") as f:
    offers = f.readlines()

offers_info = []
for offer in offers:
    offer_id = offer.split(" ")[0]
    server_id = offer.split(" ")[1]
    side = offer.split(" ")[-1]
    offer_info = {"offer_id": offer_id, "server_id": server_id, "side": side.strip()}
    offers_info.append(offer_info)

with open("offers_ids.json", "w") as f:
    json.dump(offers_info, f)
