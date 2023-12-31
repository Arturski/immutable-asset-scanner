# Immutable X (StarkEx) - Asset Scanner Script

## Summary

This script is designed to validate asset data retrieved from an API. It checks for null values, tests the responsiveness of URLs, and ensures that metadata is set correctly. Additionally, it provides statistics about the validation results.

## Help Menu

To see the help menu and understand the available options, use the following command:

```bash
python assetScanner.py -h
```

## How to Run

### macOS, Linux, and Windows

1. **Clone the Repository:** Clone this repository to your local machine.

```bash
git clone https://github.com/Arturski/immutable-asset-scanner.git
```

2. **Navigate to the Script Directory:** Use the `cd` command to enter the script directory.

```bash
cd immutable-asset-scanner
```

3. **Install Required Libraries:** If you haven't already, install the required Python libraries. You can use `pip` for this.

```bash
pip install requests
```

4. **Run the Script:** Execute the script by running the following command, replacing the placeholders with your API URL and the desired number of worker processes:


Replace `"YOUR_API_URL_HERE"` with the actual API URL you want to query and `NUMBER_OF_WORKERS_HERE` with the desired number of worker processes. An optional valye of `TEST_ID` is possible if you are running multiple tests if not set `output_default.json`

```bash
python assetScanner.py -q "YOUR_API_URL_HERE" -w NUMBER_OF_WORKERS_HERE -i "TEST_ID"

python3 assetScanner.py -q "https://api.sandbox.x.immutable.com/v1/assets?page_size=200&order_by=updated_at&direction=desc&collection=0xea152929e1a46eaa53a6c48d072bcc8e6ffcca1b" -w 5 -i "full_collection_run"
```


`-q`, `--query_url`: Immutable X Asset API Url ref: https://docs.immutable.com/x/reference/#/operations/listAssets

`-w`, `--num_workers`: every item is pulled that is pulled from the assets api is placed in a queue, each worker scans one item at a time. Consider rate limitations when setting this url tests have a 5 retry, 5s exponential backoff (5, 5*2, 10*2..)

`-i`, `--testID`: Optional string to accompany the output file


You can wrap the script in a a line of bash if you want to batch process multiple collections or asset buckets

```bash
for i in 0xea152929e1a46eaa53a6c48d072bcc8e6ffcca1b 0x94cdf05eddd0764b6d58751e0370b6de0d4e713a ; do 
    echo $i;  
    python3 assetScanner.py -q "https://api.sandbox.x.immutable.com/v1/assets?page_size=200&order_by=updated_at&direction=desc&collection=${i}" -w 5 -i ${i} ; 
done 
```

or from a file

```bash
while read i; do 
    echo $i;  
    python3 assetScanner.py -q "https://api.sandbox.x.immutable.com/v1/assets?page_size=200&order_by=updated_at&direction=desc&collection=${i}" -w 5 -i ${i} ; 
done < ./collection-list.txt
```

Sample console output:

```bash
Starting  5  workers..

Collector started, reading data from API
Imported 20 tokens

Total number of tokens scanned: 20
Total tokens with null value problems: 20
Total tokens with bad url problem: 5
Total tokens with missing metadata: 0

Top 5 field names with null values:
uri: 20

Top 5 Token IDs with URL errors:
4: 2
2: 2
17: 2
12: 2
18: 2

Top 5 Token IDs with missing metadata:
Report saved to output-0x6a44969e9f98afb70353e6358e7aec4290baac7a.json
```