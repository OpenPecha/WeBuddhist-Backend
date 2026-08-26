import requests
from pathlib import Path

# URL_TEMPLATE = "http://www.kalacakra.org/calendar/tdata/pl_{year}.txt"
URL_TEMPLATE = "http://www.kalacakra.org/calendar/tdata/ts_{year}.txt"

def download_calendar_data(out_dir: str, years: range) -> None:
    """
    Download Tibetan calendar data for each year from kalacakra.org
    and write one txt file per year.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    for year in years:
        url = URL_TEMPLATE.format(year=year)
        response = requests.get(url)
        response.raise_for_status()

        file_path = Path(out_dir) / f"{year}.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"Downloaded {year} from {url}")


if __name__ == "__main__":
    out_dir = "calendar_split_years"
    years = range(1800, 2050)  # 2001 to 2049 inclusive
    download_calendar_data(out_dir, years)
    print("Calendar data downloaded and saved to", out_dir)
