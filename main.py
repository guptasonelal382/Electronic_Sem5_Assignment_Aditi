import requests
import os
from collections import defaultdict


# ==========================================================
# CONFIGURATION
# ==========================================================

# Elexon public API
ELEXON_URL = (
    "https://data.elexon.co.uk/"
    "bmrs/api/v1/datasets/FUELINST/stream"
)

# YOUR THINGSPEAK CHANNEL
THINGSPEAK_CHANNEL = 3457089

# Your ThingSpeak Write API Key
# This comes from GitHub Secrets
THINGSPEAK_WRITE_KEY = os.environ.get(
    "THINGSPEAK_WRITE_KEY"
)


# ==========================================================
# GET DATA FROM ELEXON
# ==========================================================

def get_elexon_data():

    print("Connecting to Elexon...")

    response = requests.get(
        ELEXON_URL,
        timeout=30
    )

    print(
        "Elexon HTTP Status:",
        response.status_code
    )

    response.raise_for_status()

    data = response.json()

    return data


# ==========================================================
# PROCESS ELEXON DATA
# ==========================================================

def process_data(data):

    print("Processing electricity data...")

    # The stream returns a list of records.
    # Each record contains:
    # startTime
    # fuelType
    # generation

    records = data

    if isinstance(data, dict):

        records = data.get("data", [])

    if not records:

        raise Exception(
            "Elexon returned no electricity data."
        )


    # ------------------------------------------------------
    # Find the latest timestamp
    # ------------------------------------------------------

    latest_time = max(
        record["startTime"]
        for record in records
        if record.get("startTime")
    )


    latest_records = [
        record
        for record in records
        if record.get("startTime") == latest_time
    ]


    # ------------------------------------------------------
    # Group generation by fuel type
    # ------------------------------------------------------

    generation = defaultdict(float)


    for record in latest_records:

        fuel = record.get("fuelType")

        value = record.get("generation")


        if fuel is None:
            continue

        if value is None:
            continue


        generation[fuel] += float(value)


    # ------------------------------------------------------
    # Calculate totals
    # ------------------------------------------------------

    total_generation = sum(
        generation.values()
    )


    renewable_fuels = [
        "WIND",
        "SOLAR",
        "HYDRO",
        "BIOMASS"
    ]


    renewable_generation = sum(
        generation.get(fuel, 0)
        for fuel in renewable_fuels
    )


    renewable_percentage = 0


    if total_generation > 0:

        renewable_percentage = (
            renewable_generation
            / total_generation
        ) * 100


    # ------------------------------------------------------
    # Individual values
    # ------------------------------------------------------

    wind = generation.get(
        "WIND",
        0
    )

    solar = generation.get(
        "SOLAR",
        0
    )

    nuclear = generation.get(
        "NUCLEAR",
        0
    )

    gas = generation.get(
        "CCGT",
        0
    )

    hydro = generation.get(
        "HYDRO",
        0
    )


    return {

        "time": latest_time,

        "total": total_generation,

        "renewable": renewable_generation,

        "renewable_percentage":
            renewable_percentage,

        "wind": wind,

        "solar": solar,

        "nuclear": nuclear,

        "gas": gas,

        "hydro": hydro
    }


# ==========================================================
# DISPLAY DATA
# ==========================================================

def display_data(result):

    print()
    print(
        "======================================"
    )

    print(
        "       ELEXON ELECTRICITY DATA"
    )

    print(
        "======================================"
    )

    print()

    print(
        "Time:",
        result["time"]
    )

    print(
        "Total Generation:",
        round(result["total"], 2),
        "MW"
    )

    print(
        "Renewable Generation:",
        round(result["renewable"], 2),
        "MW"
    )

    print(
        "Renewable Percentage:",
        round(
            result["renewable_percentage"],
            2
        ),
        "%"
    )

    print()

    print(
        "Wind:",
        round(result["wind"], 2),
        "MW"
    )

    print(
        "Solar:",
        round(result["solar"], 2),
        "MW"
    )

    print(
        "Hydro:",
        round(result["hydro"], 2),
        "MW"
    )

    print(
        "Nuclear:",
        round(result["nuclear"], 2),
        "MW"
    )

    print(
        "Gas:",
        round(result["gas"], 2),
        "MW"
    )


# ==========================================================
# SEND DATA TO THINGSPEAK
# ==========================================================

def send_to_thingspeak(result):

    print()
    print("Uploading data to ThingSpeak...")


    if not THINGSPEAK_WRITE_KEY:

        raise Exception(
            "THINGSPEAK_WRITE_KEY is missing."
        )


    payload = {

        "api_key":
            THINGSPEAK_WRITE_KEY,

        # Field 1
        "field1":
            round(result["total"], 2),

        # Field 2
        "field2":
            round(result["renewable"], 2),

        # Field 3
        "field3":
            round(result["wind"], 2),

        # Field 4
        "field4":
            round(result["solar"], 2),

        # Field 5
        "field5":
            round(result["nuclear"], 2),

        # Field 6
        "field6":
            round(
                result["renewable_percentage"],
                2
            ),

        # Field 7
        "field7":
            round(result["gas"], 2)
    }


    response = requests.post(
        "https://api.thingspeak.com/update",
        data=payload,
        timeout=30
    )


    response.raise_for_status()


    print(
        "ThingSpeak Response:",
        response.text
    )


    if response.text == "0":

        raise Exception(
            "ThingSpeak rejected the update."
        )


    print()
    print(
        "======================================"
    )

    print(
        "       UPLOAD SUCCESSFUL"
    )

    print(
        "======================================"
    )

    print(
        "Channel:",
        THINGSPEAK_CHANNEL
    )

    print(
        "Entry ID:",
        response.text
    )


# ==========================================================
# MAIN
# ==========================================================

def main():

    print()
    print(
        "SMART ELECTRICITY MONITOR"
    )

    print(
        "Source: Elexon"
    )

    print(
        "Destination: ThingSpeak 3457089"
    )

    print()


    # 1. Get Elexon data

    data = get_elexon_data()


    # 2. Process data

    result = process_data(data)


    # 3. Display

    display_data(result)


    # 4. Upload

    send_to_thingspeak(result)


# ==========================================================
# START PROGRAM
# ==========================================================

if __name__ == "__main__":

    main()
