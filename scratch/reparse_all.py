from swim_parser.batch_parse import batch_parse

print("Starting batch parsing of all seasons...")

print("\n--- Parsing 2023_2024 ---")
batch_parse("2023_2024")

print("\n--- Parsing 2024_2025 ---")
batch_parse("2024_2025")

print("\n--- Parsing historical/extracted ---")
batch_parse("historical/extracted")

print("\n--- Parsing 2025_2026 ---")
batch_parse("2025_2026")

print("\nAll batch parsing tasks completed!")
