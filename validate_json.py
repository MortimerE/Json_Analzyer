import json
import os
import pandas as pd
import re
import sys
#from prompt_toolkit import Application
#from prompt_toolkit.key_binding import KeyBindings
#from prompt_toolkit.layout import Layout
#from prompt_toolkit.widgets import RadioList
#from prompt_toolkit.shortcuts import clear

def normalize_biomarker(name):
    # Normalize to lower case
    name = name.lower()
    # Remove extra spaces and keep parentheses content
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def anti_alias(mark, normalized_dict, biomarker_database):
    markers = list(biomarker_database.keys())
    keys = list(normalized_dict.keys())
    names = dict(zip(keys, markers))
    return names[mark]
def load_biomarker_database(csv_file_path):
    df = pd.read_csv(csv_file_path)
    biomarker_database = {}
    for index, row in df.iterrows():
        biomarker = row['Biomarker']
        units = row['Units']
        units_list = []
        if pd.notna(units):  # Check if units column is not NaN
            unit_parts = units.split(', ')
            for unit in unit_parts:
                match = re.match(r"^[\"']?([^\s\"'\(\)\[\]]+)[\"']?", unit)
                if match:
                    units_list.append(match.group(0))
                else:
                    units_list.append('')  # Append empty string if no match found
        biomarker_database[biomarker] = units_list, units

    return biomarker_database

def process_and_validate(json_file_path, biomarker_database):
    try:
        with open(json_file_path, 'r') as file:
            biomarker_data = json.load(file)
    except Exception as e:
        return f"An error occurred while reading the file: {e}"

    # Normalized dictionary with simplified biomarker names
    normalized_dict = {normalize_biomarker(b): v for b, v in biomarker_database.items()}

    valid_biomarkers_report = []
    invalid_biomarkers_report = []
    biomarkers_with_invalid_units_report = []
    aliased_biomarkers_report = []
    double_invalid_report = []

    flag = True

    for entry in biomarker_data:
        biomarker = entry['biomarker']
        unit = entry['unit']
        if biomarker in biomarker_database:
            if unit in biomarker_database[biomarker][0]:
                valid_biomarkers_report.append(entry)
                flag = False
            else:
                biomarkers_with_invalid_units_report.append(
                    f"{biomarker}: Invalid unit '{unit}', valid units are {biomarker_database[biomarker][1]}"
                )
                flag = False
        else:
            #invalid_biomarkers_report.append(biomarker)
            input_biomarker = normalize_biomarker(biomarker)
            for valid_mark in normalized_dict:
                # Check if any biomarker key is contained within the input
                if input_biomarker in valid_mark or input_biomarker == valid_mark:
                    label = anti_alias(valid_mark, normalized_dict, biomarker_database)
                    aliased_biomarkers_report.append(
                        f"{biomarker}: Invalid name, correct to {label}")
                    flag = False
                    if unit not in normalized_dict[valid_mark][0]:
                    #else:
                        #flag = False
                        double_invalid_report.append(
                            f"{biomarker}: Invalid unit '{unit}', valid units are {biomarker_database[label][1]}"
                        )
                    break

    #"""
    #for entry in biomarker_data:
    #    biomarker = entry['biomarker']
    #    unit = entry['unit']

        if flag:
            invalid_biomarkers_report.append(biomarker)
    #"""

    report = {
        'total_valid_biomarkers': len(valid_biomarkers_report),
        'total_invalid_biomarkers': len(invalid_biomarkers_report) + len(aliased_biomarkers_report) + len(biomarkers_with_invalid_units_report),
        'invalid_biomarkers': invalid_biomarkers_report,
        'biomarkers_with_invalid_units': biomarkers_with_invalid_units_report,
        'aliased_biomarkers': aliased_biomarkers_report,
        'invalid_biomarkers_with_invalid_units': double_invalid_report
    }

    return report

def print_report(report):
    print("\nInvalid Json:")
    for biomarker in report['invalid_biomarkers']:
        print(f"  - {biomarker}")
    if len(report['invalid_biomarkers']) <= 0: print("None")
    print("\nValid Biomarkers with Invalid Units:")
    for entry in report['biomarkers_with_invalid_units']:
        print(f"  - {entry}")
    if len(report['biomarkers_with_invalid_units']) <= 0: print("None")
    print("\nMislabeled Valid Biomarkers:")
    for e in report['aliased_biomarkers']:
        print(f"  - {e}")
    for e in report['invalid_biomarkers_with_invalid_units']:
        print(f"  - {e}")
    if len(report['aliased_biomarkers']) <= 0: print("None")
    print(f"\nTotal Valid: {report['total_valid_biomarkers']}")
    print(f"Total Invalid: {report['total_invalid_biomarkers']}\n")


def select_file(directory):
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.endswith('.txt')]
    for i, file in enumerate(files):
        print(f"{i + 1}: {file}")
    choice = int(input("Select a file by number: ")) - 1
    return os.path.join(directory, files[choice])


def main():
    csv_file_path = input("Enter the file path to the CSV file containing the biomarker database: ")
    #csv_file_path = "vaclav_dictionary.csv"
    directory = input("Enter the directory path containing the JSON files: ")
    #directory = "robot_jsons"
    if not os.path.isdir(directory) or not os.path.isfile(csv_file_path):
        print("The provided path is not valid.")
        return

    biomarker_database = load_biomarker_database(csv_file_path)

    while True:
        #try:
        selected_file = select_file(directory)
        validation_report = process_and_validate(selected_file, biomarker_database)
        print_report(validation_report)
        input("Press Enter to return to file selection...")
        #except Exception as e:
        #    print(f"Error: {e}")
        #    input("Press Enter to try again...")

if __name__ == "__main__":
    main()