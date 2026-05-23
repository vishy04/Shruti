from src.extractor import extract_order

transcript = " पिरेंका तिवारी 30 माई 38, 35, 42, 49, 40, सलवार सेंति 30, 15"

order = extract_order(transcript)

print(order.model_dump_json(indent=2))