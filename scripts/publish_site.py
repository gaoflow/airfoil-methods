from pathlib import Path
import shutil
import subprocess

project_root = Path(__file__).resolve().parents[1]
repository_root = project_root.parents[1]
lab_destination = repository_root / "site" / "public" / "labs" / "airfoil-methods"
image_destination = repository_root / "site" / "public" / "images" / "projects" / "airfoil-methods"
document_destination = repository_root / "site" / "public" / "documents"

if lab_destination.exists():
    shutil.rmtree(lab_destination)
shutil.copytree(project_root / "demo", lab_destination)
image_destination.mkdir(parents=True, exist_ok=True)
for name in ("lift-validation.svg", "pressure-and-refinement.svg", "drag-blind-spot.svg"):
    shutil.copy2(project_root / "results" / name, image_destination / name)
document_destination.mkdir(parents=True, exist_ok=True)
shutil.copy2(project_root / "report.css", document_destination / "airfoil-methods-report.css")
subprocess.run([
    "pandoc",
    str(project_root / "REPORT.md"),
    "--standalone",
    "--mathml",
    "--metadata",
    "title=Airfoil Methods technical report",
    "--css=/documents/airfoil-methods-report.css",
    "--output",
    str(document_destination / "airfoil-methods-report.html"),
], check=True)
print(f"Published airfoil explorer to {lab_destination.relative_to(repository_root)}")
print(f"Published airfoil figures to {image_destination.relative_to(repository_root)}")
print(f"Published airfoil report to {(document_destination / 'airfoil-methods-report.html').relative_to(repository_root)}")
