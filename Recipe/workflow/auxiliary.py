"""
This module contains auxiliary functions for that helps managing files such as clearing directories and copying files.
"""
import os
import shutil
from .slicer import single, multiplex
import zipfile
import json
from collections import Counter

def clear_dir(output_dir: str) -> None:
    """
    Removes all directories in the specified output directory, 
    except those named '.gitignore'.

    Args:
        output_dir (str): The path to the output directory to clean.

    Returns:
        None
    """
    for item in os.listdir(output_dir):
        item_path = os.path.join(output_dir, item)
        if os.path.isdir(item_path) and item != '.gitignore':
            shutil.rmtree(item_path)


def data_slicer(base_dir: str = 'Data/', show_error: bool = False) -> None:
    """
    Processes the data folders for yadg/dgpost status, printing the results for each unit.
    
    Args:
        base_dir (str, optional): The base directory containing data folders. Defaults to 'Data/'.
        show_error (bool, optional): Flag to indicate whether errors from single.stage_manager and multiplex.stage_manager
        should be shown or not. Defaults to False.
    
    Returns:
        None
    """
    print('Data slicing or preparation for yadg,dgpost status: \n')
    
    dirs = [d for d in os.listdir(base_dir) if d != '.DS_Store' and d != 'holder.gitignore']
    
    for file in sorted(dirs):
        print('------------------------------------------------------------------')
        print('Folder: ', file)
        folder_path = os.path.join(base_dir, file)
        
        if file.startswith('Multiplex'):
            status_report = multiplex.stage_manager(folder_path, folder_name=file, show_error=show_error)
        else:
            status_report = single.stage_manager(folder_path, folder_name=file, show_error=show_error)
        
        for unit, status in status_report.items():
            print(f'Successfully sliced: {", ".join(status["pass"])}')
            
            if status["failed"]:
                print(f'Failed to slice: {", ".join(status["failed"])}')

            if status['proceed']:
                print(f'{unit} will be subjected to yadg/dgpost')
            else:
                print(f'!! WARNING: {unit} will NOT be subjected to yadg/dgpost')
            print()
        
        print('------------------------------------------------------------------')


def update_gc_zip_annotation(
    data_folder_dir: str, annotation_name: str, sequence_location: str
) -> None:
    """
    Update annotations in a zip file ending with "-GC.zip" within a given directory.

    Args:
        data_folder_dir (str): Directory containing the data folder.
        annotation_name (str): New value for the "name" field in "annotations".
        sequence_location (str): New value for the "location" field in "sequence".
    """
    # Step 1: Locate the zip file ending with "-GC.zip"
    zip_file_path = None
    for root, _, files in os.walk(data_folder_dir):
        for file in files:
            if file.endswith("-GC.zip"):
                zip_file_path = os.path.join(root, file)
                break
        if zip_file_path:
            break

    if not zip_file_path:
        print("No zip file ending with '-GC.zip' found in the specified directory.")
        return

    print(f"Located zip file: {zip_file_path}")

    # Step 2: Define a temporary directory for unzipping
    temp_dir = os.path.join(data_folder_dir, "temp_unzip")

    try:
        # Ensure the temporary directory is empty before processing
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        # Step 3: Unzip the file
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Step 4: Update the annotations in all .fusion-data files
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(".fusion-data"):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Update the "name" field in "annotations"
                    if "annotations" in data and isinstance(data["annotations"], dict):
                        data["annotations"]["name"] = annotation_name

                    # Update the "location" field in "sequence"
                    if "sequence" in data and isinstance(data["sequence"], dict):
                        data["sequence"]["location"] = sequence_location

                    # Save the updated content back to the file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4)

        # Step 5: Rezip the content back and overwrite the original zip file
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    zip_ref.write(file_path, os.path.relpath(file_path, temp_dir))

        print(f"Updated zip file saved at: {zip_file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Step 6: Clean up temporary files and directories
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        print("Temporary files cleaned up.")


def analyze_annotations(data_folder_dir: str) -> None:
    """
    Analyze and print the occurrences of unique values in "annotations:name" and "sequence:location"
    within the first zip file ending with "-GC.zip" found in the given directory.

    Args:
        data_folder_dir (str): Directory containing the data folder.
    """
    # Step 1: Locate the zip file ending with "-GC.zip"
    zip_file_path = None
    for root, _, files in os.walk(data_folder_dir):
        for file in files:
            if file.endswith("-GC.zip"):
                zip_file_path = os.path.join(root, file)
                break
        if zip_file_path:
            break

    if not zip_file_path:
        print("No zip file ending with '-GC.zip' found in the specified directory.")
        return

    print(f"Located zip file: {zip_file_path}")

    # Step 2: Initialize counters for annotations:name and sequence:location
    name_counter = Counter()
    location_counter = Counter()

    # Step 3: Analyze the contents of the zip file
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            for file_name in zip_ref.namelist():
                # Only process .fusion-data files
                if file_name.endswith(".fusion-data"):
                    with zip_ref.open(file_name) as file:
                        try:
                            # Load JSON and extract fields
                            data = json.load(file)
                            
                            # Count occurrences of "annotations:name"
                            if "annotations" in data and isinstance(data["annotations"], dict):
                                name = data["annotations"].get("name", "No name field found")
                                name_counter[name] += 1

                            # Count occurrences of "sequence:location"
                            if "sequence" in data and isinstance(data["sequence"], dict):
                                location = data["sequence"].get("location", "No location field found")
                                location_counter[location] += 1

                        except json.JSONDecodeError:
                            # Skip files that are not valid JSON
                            print(f"File {file_name} is not a valid JSON format.")
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    # Step 4: Print the variety and occurrences of annotations:name and sequence:location
    print("\nOccurrences of annotations:name:")
    for name, count in name_counter.items():
        print(f"  Name: {name} : Occurrence: {count}")

    print("\nOccurrences of sequence:location:")
    for location, count in location_counter.items():
        print(f"  Location: {location} : Occurrence: {count}")


def zip_folder(output_folder: str = './Output', zip_name: str = './Output/output.zip') -> None:
    """
    Compresses the specified folder into a ZIP archive, excluding designated files.

    Args:
        output_folder (str, optional): Path to the folder to compress. Defaults to './Output'.
        zip_name (str, optional): Path and filename for the resulting ZIP archive. Defaults to './Output/output.zip'.

    Returns:
        None
    """
    # List files to be zipped, excluding holder.gitignore
    files_to_zip = []
    for root, _, files in os.walk(output_folder):
        for file in files:
            if file == "holder.gitignore":
                continue
            file_path = os.path.join(root, file)
            files_to_zip.append((file_path, os.path.relpath(file_path, start=output_folder)))

    # Create the ZIP file and add files from the pre-gathered list
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path, arcname in files_to_zip:
            zipf.write(file_path, arcname=arcname)

    print(f"Zipping complete. Archive saved as {zip_name}.")


def unzip_and_organize(data_folder: str = "/home/jovyan/work/test-autoplotdb/AutoplotDB/Data") -> None:
    """
    Unzips all .zip files in a specified directory, ensuring correct extraction:
    - If a ZIP contains a single folder with the same name as the ZIP, extract only its contents.
    - If a ZIP contains multiple folders/files, extract them directly into data_folder.
    """
    # Collect all .zip files in the directory
    zip_files = glob.glob(f"{data_folder}/*.zip")

    for zip_file in zip_files:
        # Define a temporary extraction folder
        temp_extract_folder = os.path.join(data_folder, "temp_extraction")
        os.makedirs(temp_extract_folder, exist_ok=True)
        
        print(f"Unzipping {zip_file} into temporary directory...")

        # Unzip into the temporary directory
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_folder)

        # Get ZIP file's base name (without .zip)
        zip_name = os.path.splitext(os.path.basename(zip_file))[0]

        # Get list of extracted items
        extracted_items = os.listdir(temp_extract_folder)

        # Case 1: ZIP contains a single folder with the same name as the ZIP
        if len(extracted_items) == 1 and extracted_items[0] == zip_name:
            extracted_folder_path = os.path.join(temp_extract_folder, zip_name)
            extracted_contents = os.listdir(extracted_folder_path)

            final_folder = os.path.join(data_folder, zip_name)

            # Remove any existing folder with the same name
            if os.path.exists(final_folder):
                shutil.rmtree(final_folder)

            # Move the entire extracted folder to the main directory
            shutil.move(extracted_folder_path, final_folder)

        else:
            # Case 2: ZIP contains multiple folders/files -> Extract them directly
            for item in extracted_items:
                shutil.move(os.path.join(temp_extract_folder, item), data_folder)

        # Delete the original zip file and temporary extraction folder
        os.remove(zip_file)
        shutil.rmtree(temp_extract_folder)

        print(f"Successfully extracted {zip_file} into {data_folder}")

