import multiprocessing
import requests
import json
import re
import argparse
import time
from collections import Counter

def test_item(item):
    token_id = item.get("token_id")
    problems = []

    # Test for null values
    for key, value in item.items():
        if value is None:
            problems.append({"key": key, "problem": "null value"})

    # Test for unresponsive URLs with a timeout of 5 seconds
    url_keys = find_url_keys(item)
    for key in url_keys:
        value = item[key]
        if value:
            url_problem = test_url(value)
            if url_problem:
                problems.append({"key": key, "problem": "bad url", "url": value, "error": url_problem})

    # Test for metadata not set
    if "metadata" not in item or not item["metadata"]:
        problems.append({"key": "metadata", "problem": "metadata not set"})

    return {"token_id": token_id, "problems": problems}

def test_url(url, timeout=5, retries=5):
    consecutive_failures = 0
    backoff_time = 5  # Initial backoff time in seconds

    for _ in range(retries):
        try:
            response = requests.get(url, allow_redirects=True, timeout=timeout)
            # Check if the response status code is in the 2xx range (indicating success)
            if 200 <= response.status_code < 300:
                return None  # No problem, URL is responsive
            else:
                return f"HTTP Error {response.status_code}"  # URL returned an HTTP error
        except Exception as e:
            consecutive_failures += 1

            # Calculate the backoff time with exponential increase
            backoff_time *= 2  # Double the backoff time on each failure

            # Print a message when rate limit is reached and backing off
            print(f"Worker: Request limit reached, backing off for {backoff_time} seconds")
            print(url)

            # Wait for the calculated backoff time before retrying
            time.sleep(backoff_time)

    return "Unresponsive URL"  # URL did not respond successfully


def find_url_keys(item):
    url_keys = []
    for key, value in item.items():
        if isinstance(value, str) and is_url(value):
            url_keys.append(key)
    return url_keys

def is_url(url):
    # Check if the string matches the pattern of a typical URL
    return bool(re.match(r'https?://\S+', url))

def getData(base_url, cursor=None):
    if cursor:
        url = f"{base_url}&cursor={cursor}"
    else:
        url = base_url

    payload = {}
    headers = {
        'Accept': 'application/json'
    }

    for _ in range(3):
        try:
            response = requests.request("GET", url, headers=headers, data=payload)
            # Check if the response status code is OK (200) and if there is content
            if response.status_code == 200 and response.content:
                return response.json()
        except Exception:
            # Wait for half a second before retrying
            time.sleep(0.5)

    return None

def collector(queue, base_url):
    total = 0
    url = base_url
    print("Collector started, reading data from API")
    while True:
        data = getData(url)
        if data is None:
            # Handle the case when data is not retrieved successfully
            continue

        for i in data['result']:
            # Enqueue the asset data to the local queue
            queue.put(i)
            total += 1
        if data['remaining'] == 0:
            print('Imported ' + str(total) + ' tokens')
            # Use a sentinel value to signal the worker processes to exit
            queue.put(None)
            break
        else:
            url = f"{base_url}&cursor={data['cursor']}"

def worker(queue, output_list):
    while True:
        data = queue.get()
        if data is None:
            # Exit the worker process when the sentinel value is received
            break

        # Perform the tests on the data
        test_results = test_item(data)

        # Add the test results to the output list
        output_list.append(test_results)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    manager = multiprocessing.Manager()

    parser = argparse.ArgumentParser(description='Asset Validation Script')
    parser.add_argument('-q', '--query_url', required=True, help='Query URL for the API')
    parser.add_argument('-w', '--num_workers', type=int, required=True, help='Number of worker processes. Consider request limits of APIs when setting this')
    parser.add_argument('-i', '--testID', default='default', help='Test ID to append to the output filename if not set will be output-default.json')


    args = parser.parse_args()

    api_url = args.query_url
    num_collector_processes = 1
    num_worker_processes = args.num_workers
    if args.testID:
        test_id = args.testID.replace('"','')  # Get the testID from the command line
    else:
        test_id = "default"

    queue = manager.Queue()
    output_list = multiprocessing.Manager().list()

    collector_processes = []
    worker_processes = []

    for _ in range(num_collector_processes):
        collector_process = multiprocessing.Process(target=collector, args=(queue, api_url))
        collector_process.start()
        collector_processes.append(collector_process)

    print("Starting ",num_worker_processes, " workers..\n" )
    for _ in range(num_worker_processes):
        worker_process = multiprocessing.Process(target=worker, args=(queue, output_list))
        worker_process.start()
        worker_processes.append(worker_process)

    # Wait for all collector processes to finish
    for process in collector_processes:
        process.join()

    # Signal worker processes to exit
    for _ in range(num_worker_processes):
        queue.put(None)

    # Wait for all worker processes to finish
    for process in worker_processes:
        process.join()

    formatted_output = list(output_list)

    total_tokens_scanned = len(output_list)
    total_null_value_problems = sum(1 for item in output_list if any(p["problem"] == "null value" for p in item["problems"]))
    total_bad_url_problems = sum(1 for item in output_list if any(p["problem"] == "bad url" for p in item["problems"]))
    total_missing_metadata_problems = sum(1 for item in output_list if any(p["problem"] == "metadata not set" for p in item["problems"]))

    # Find the top 5 field names with null values
    null_value_counts = Counter(p["key"] for item in output_list for p in item["problems"] if p["problem"] == "null value")
    top_5_null_value_fields = null_value_counts.most_common(5)

    # Find the top 5 token IDs with URL errors
    error_token_counts = Counter(item["token_id"] for item in output_list for p in item["problems"] if p["problem"] == "null value" or p["problem"] == "bad url" or p["problem"] == "metadata not set")
    top_5_error_token_ids = error_token_counts.most_common(5)

    # Find the top 5 token IDs with missing metadata
    missing_metadata_counts = Counter(item["token_id"] for item in output_list for p in item["problems"] if p["problem"] == "metadata not set")
    top_5_missing_metadata_token_ids = missing_metadata_counts.most_common(5)


    # Print the statistics
    print("\nTotal number of tokens scanned:", total_tokens_scanned)
    print("Total tokens with null value problems:", total_null_value_problems)
    print("Total tokens with bad url problem:", total_bad_url_problems)
    print("Total tokens with missing metadata:", total_missing_metadata_problems)
    print("\nTop 5 field names with null values:")
    for field, count in top_5_null_value_fields:
        print(f"{field}: {count}")
    print("\nTop 5 Token IDs with URL errors:")
    for field, count in top_5_error_token_ids:
        print(f"{field}: {count}")
    print("\nTop 5 Token IDs with missing metadata:")
    for field, count in top_5_missing_metadata_token_ids:
        print(f"{field}: {count}")
    # Save the output list as a formatted JSON file locally
    output_filename = f'output-{test_id}.json'
    with open(output_filename, 'w', encoding='utf-8') as json_file:
        json.dump(formatted_output, json_file, indent=2)

    print(f"Report saved to {output_filename}")
