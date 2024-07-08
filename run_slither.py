import csv
import json
import os
import re
import sys
import docker

def get_pragma(sc_file):
    with open(sc_file, "r") as f:
        sol_txt = f.read()
    pattern = r"(?<=pragma solidity ).*;"
    regex = re.search(pattern, sol_txt)
    pragma = regex.group(0)[1:-1] if regex.group().startswith('^') else str(regex.group(0)[:-1])
    if int(pragma.split(".")[1]) == 4 and int(pragma.split(".")[2]) < 11:
        pragma = "0.4.11"
    print(f"Pragma: {pragma}")
    return pragma

def run_slither(sc_file, input_dir):
        sc_file = os.path.abspath(sc_file)
        input_dir = os.path.abspath(input_dir)

        client = docker.from_env()

        # Get docker container instance, else create it
        try:
            container = client.containers.get("slither")
        except docker.errors.NotFound:
            host_path, container_path = input_dir, "/home/ethsec/shared"
            volumes = {host_path: {'bind': container_path, 'mode': 'rw'}}

            container = client.containers.create(
                image="trailofbits/eth-security-toolbox",
                name="slither",
                volumes=volumes,
                stdin_open=True,
            )

        if container.status == "running":
            print(f"Docker container '{container.name}' is running")
        else:
            print(f"Docker container '{container.name}' is in status '{container.status}'\nStarting container...")
            container.start()
            print(f"New state '{container.status}'")
        cmd = lambda sol_file, pragma: [f"solc-select use --always-install {pragma}", f"slither shared/{sol_file} --json -"]
        pragma = get_pragma(sc_file)
        if int(pragma.split(".")[1]) == 4 and int(pragma.split(".")[2]) < 24:
            pragma = "0.4.24"
        sol_file = sc_file.split(input_dir)[-1]
        cmd = cmd(sol_file, pragma)
        if isinstance(cmd, list):
            for c in cmd:
                print(f"Running command: {c}")
                exit_code, output = container.exec_run(cmd=c, stdout=True, stderr=True, stream=False)
        else:
            raise Exception("Command must be a list of strings")
        
        try:
            out = json.loads(output)
        except json.JSONDecodeError:
            print(f"exit code:{exit_code}")
            print(f"Output is not a valid JSON: {output}")
            output = {"error": "Output is not a valid JSON"}
            return -1, output

        return exit_code, out

def filter_vulns(data, level="Medium"):
    severity = {
        "High": ["High"],
        "Medium": ["High", "Medium"],
        "Low": ["High", "Medium", "Low"]
    }
    if data.get("results", False).get("detectors", False):
        vulns = list(map(lambda x: {key: x[key] for key in ["description", "check", "impact", "confidence","first_markdown_element"]}, 
                            data["results"]["detectors"]))
        filtered = list(filter(lambda x: x["impact"] in severity[level], vulns))
        return filtered

def run_on_results(results):
    exit_codes = []
    with open(os.path.join(results, "compilation_results_0.4.24.csv"), "r") as fin:
        entries = csv.reader(fin)
        next(entries)
        for entry in entries:
            if entry[1] == "1":
                continue
            print(entry[0])
            fullpath = os.path.join(results, entry[0])
            exit_code, output = run_slither(fullpath, results)
            raw = fullpath.replace(".sol", "_vulns.json")
            exit_codes.append((fullpath, exit_code))
            if exit_code == -1:
                print(f"Error running Slither on {fullpath}")
                continue
            with open(raw, "w") as f:
                json.dump(output, f, indent=4)

            filtered = fullpath.replace(".sol", "_vulns_Medium.json")
            vulns = filter_vulns(output)
            with open(filtered, "w") as f:
                json.dump(vulns, f, indent=4)
    with open(os.path.join(results, "patches_exit_codes.cvs"), "w") as f:
        for file, code in exit_codes:
            f.write(f"{file},{code}\n")

def main():
    results = sys.argv[1]
    run_on_results(results)

if __name__ == "__main__":
    main()
