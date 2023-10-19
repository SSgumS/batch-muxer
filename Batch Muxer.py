import os
import argparse
import subprocess
import re
import zlib


input_placeholder = "{input}"
output_placeholder = "{output}"


def run_command(input: str, output: str, command: str):
    subprocess.run(
        command.replace(input_placeholder, input).replace(output_placeholder, output),
        shell=True,
    )


def get_crc(file_path: str):
    with open(file_path, "rb") as file:
        file_content = file.read()
        crc = zlib.crc32(file_content)
    return f"{crc:08X}"


def add_before_extension(path: str, postfix: str):
    path = re.sub(r"\.mkv$", f"{postfix}.mkv", path)
    return path


def remove_before_extension(path: str, postfix: str, escape: bool = True):
    regex_postfix = postfix
    if escape:
        regex_postfix = re.escape(postfix)
    path = re.sub(regex_postfix + r"\.mkv$", ".mkv", path)
    return path


def ensure_space(path: str):
    if path[-5:] != " .mkv":
        path = re.sub(r"\.mkv$", " .mkv", path)
    return path


# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "folder",
    help="Folder path",
)
parser.add_argument(
    "--command",
    help="Command pattern",
)
parser.add_argument(
    "--no-space-before-crc", action="store_true", help="Do not add space before crc"
)
parser.add_argument(
    "--do-not-remove-old-crc",
    action="store_true",
    help="Do not remove old crc",
)
parser.add_argument(
    "--in-place",
    action="store_true",
    help="Do jobs in-place",
)
args = parser.parse_args()

# Check command pattern
if args.command is not None:
    placeholders = [input_placeholder, output_placeholder]
    for placeholder in placeholders:
        if args.command.count(placeholder) < 1:
            raise ValueError(f"Command pattern must contain a {placeholder}!")

temp_postfix = ".temp"

for file_name in os.listdir(args.folder):
    input_path = os.path.join(args.folder, file_name)
    # Skip folders
    if os.path.isdir(input_path):
        continue
    # Create output folder
    if args.in_place:
        output_folder_path = args.folder
    else:
        output_folder_path = os.path.join(args.folder, "out")
    os.makedirs(output_folder_path, exist_ok=True)
    # Remove old crc
    if not args.do_not_remove_old_crc:
        file_name = remove_before_extension(file_name, r"\[[^]]*\]", False)
    # Set intermediate path
    if args.command is None:
        temp_path = input_path
    else:
        temp_path = os.path.join(
            output_folder_path, add_before_extension(file_name, temp_postfix)
        )
        # Mux
        run_command(input_path, temp_path, args.command)
    # Create output path (with crc)
    output_path = os.path.join(output_folder_path, file_name)
    if not args.no_space_before_crc:
        output_path = ensure_space(output_path)
    output_path = add_before_extension(output_path, f"[{get_crc(temp_path)}]")
    # Rename
    os.rename(temp_path, output_path)
