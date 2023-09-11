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
git clone https://github.com/your-username/asset-validation-script.git
```

2. **Navigate to the Script Directory:** Use the `cd` command to enter the script directory.

```bash
cd asset-validation-script
```

3. **Install Required Libraries:** If you haven't already, install the required Python libraries. You can use `pip` for this.

```bash
pip install requests
```

4. **Run the Script:** Execute the script by running the following command, replacing the placeholders with your API URL and the desired number of worker processes:

```bash
python asset_validation.py -q "YOUR_API_URL_HERE" -w NUMBER_OF_WORKERS_HERE
```

Replace `"YOUR_API_URL_HERE"` with the actual API URL you want to query and `NUMBER_OF_WORKERS_HERE` with the desired number of worker processes.