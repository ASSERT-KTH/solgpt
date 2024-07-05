import os
import subprocess

SMARTBUGS_DIR = "/home/mokita/sc_study/smartbugs-curated/dataset"

def run_solgpt(sc_file, smartbugs_dir, outdir):
    try:
        cmd = f"python solgpt_get_fix.py {sc_file} {smartbugs_dir} {outdir}"
        print(f"Running: {cmd}")
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    except Exception as e:
        print(f"Error: {e}")
    file = os.path.basename(sc_file).replace(".sol", "")
    directory = os.path.dirname(sc_file).split("/")[-1]
    output_path = os.path.join(outdir, directory, file)
    os.makedirs(output_path, exist_ok=True)
    log_file = os.path.join(output_path, f"{file}.log")
    with open(log_file, "w") as f:
        f.write(res.stderr)
    output_file = os.path.join(output_path, f"{file}.out")
    with open(output_file, "w") as f:
        f.write(res.stdout)
    return res.returncode

def run_on_smartbugs(outputdir):
    exitcodes = []
    for root, _, files in os.walk(SMARTBUGS_DIR):
        for file in files:
            print(file)
            if file.endswith(".sol"):
                exitcode = run_solgpt(os.path.join(root, file), SMARTBUGS_DIR, outputdir)
                exitcodes.append((os.path.join("smartbugs-curated/dataset", root.split("/")[-1], file), exitcode))
    with open(os.path.join(outputdir, "exitcodes.csv"), "w") as f:
        for file, code in exitcodes:
            f.write(f"{file},{code}\n")

def main():
    run_on_smartbugs("cleaned")

if __name__ == "__main__":
    main()