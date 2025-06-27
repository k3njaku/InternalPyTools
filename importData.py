import requests
import json
import csv

# URL to fetch data from
url = "https://apptrack.chiraagtracker.com/ajax?Option=FetchFilteredAppointments&Id=144&OID=1&StartDate=01-01-2025&EndDate=08-04-2025&UserId=0&DeptId=0&URUserRole=Admin&QAStatus=0&SchOnStartDate=00-00-0000&SchOnEndDate=00-00-0000&SchForStartDate=00-00-0000&SchForEndDate=00-00-0000"

# File to save the fetched data
output_csv = "output.csv"

try:
    # Send a GET request to the URL
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for HTTP errors

    # Parse the JSON response
    data = response.json()

    # Determine headers for the JSON object and additional fields
    json_keys = set()
    for record in data:
        json_keys.update(record[0].keys())
    json_keys = sorted(json_keys)

    additional_field_count = max(len(record) - 1 for record in data)
    additional_headers = [f'Extra{i}' for i in range(1, additional_field_count + 1)]

    headers = json_keys + additional_headers

    # Flatten each record into a single row
    def flatten_record(record):
        json_part = record[0]
        row = [json_part.get(key, '') for key in json_keys]
        additional_parts = record[1:]
        additional_parts += [''] * (additional_field_count - len(additional_parts))
        row.extend(additional_parts)
        return row

    flattened_data = [flatten_record(record) for record in data]

    # Write the flattened data to a CSV file
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)  # Write header row
        writer.writerows(flattened_data)

    print(f"CSV file has been created as '{output_csv}'")

except requests.exceptions.RequestException as e:
    print(f"An error occurred while fetching data: {e}")

except json.JSONDecodeError as e:
    print(f"An error occurred while parsing JSON: {e}")