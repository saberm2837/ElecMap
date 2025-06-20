# 🧠 ElecMap: Intracranial Electrode Localization Toolkit

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI version](https://badge.fury.io/py/elecmap.svg)](https://pypi.org/project/elecmap/)

Automated detection and visualization of intracranial electrodes from CT/MR scans for neurosurgical planning and research.

---

## 📁 Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Electrode Detection](#electrode-detection)
  - [Electrode Visualization](#electrode-visualization)
- [Sample Output](#sample-output)
- [Project Structure](#project-structure)
- [JSON Output Format](#json-output-format)
- [Use Cases](#use-cases)
- [Dependencies](#dependencies)
- [License](#license)
- [Contact](#contact)
- [Citation](#citation)

---

## 📘 Introduction

**ElecMap** is a Python package designed for the automated detection of intracranial electrodes from CT and MR brain scans. It accurately identifies and localizes electrode centroids within medical imaging data. The package includes a visualization tool to help users review and display the detected electrode locations.

It leverages powerful libraries such as:
- **SimpleITK** for image processing
- **nipype** for interfacing with **FSL's BET**
- **matplotlib** for report generation

---

## 🌟 Key Features

- ✅ **Precise Electrode Mapping**: Localizes electrode centroids in 3D space
- 🔄 **Multi-Modal Integration**: Combines CT and MR data for improved anatomical accuracy
- 📄 **Clinical-Grade Reports**: Generates standardized HTML reports for documentation
- 🚫 **Smart Filtering**: Automatic outlier rejection and duplicate detection
- ⚙️ **Fallback Mode**: Works with CT-only if FSL or MR scan is unavailable

---

## 📦 Installation

### 1. Install directly from PyPI (recommended):

```bash
pip install elecmap
```

### 2. Clone the repository from GitHub:

```bash
git clone https://github.com/saberm2837/ElecMap.git
cd ElecMap
```

> 🔔 **Note:** FSL must be installed and accessible in your system PATH to use MR-based skull stripping features. If unavailable, ElecMap will still perform CT-only detection with a warning.

---

## 🛠️ Usage

### 1. Electrode Detection

```python
from elecmap import detect_electrodes
import os

# Input files
ct_file = '/path/to/sample_ct.nii'
mr_file = '/path/to/sample_mr.nii'  # Optional if FSL is unavailable

# Set FSL environment variables if needed
if 'FSLDIR' not in os.environ:
    os.environ['FSLDIR'] = '/opt/fsl'
    os.environ['FSLOUTPUTTYPE'] = 'NIFTI_GZ'

# Run detection
detect_electrodes(ct_file, mr_file)
```

This function performs:
- STEP 1: Load CT and MR images
- STEP 2: Skull-strip MR using FSL BET (optional)
- STEP 3: Apply MR brain mask to CT (optional)
- STEP 4: Detect candidate electrodes from CT intensities
- STEP 5: Eliminate outliers
- STEP 6: Save coordinates to  
  `processed_scans/electrodes_sample_ct.json`

> ✅ **Tip:** If no MR image or FSL is available, simply pass `None` as the second argument or omit it.

---

### 2. Electrode Visualization

```python
from elecmap import display_electrode_locations

# Input files
ct_file = '/path/to/sample_ct.nii'
json_file = 'processed_scans/electrodes_sample_ct.json'

# Generate HTML report
display_electrode_locations(ct_file, json_file)
```

This function:
- Overlays detected electrodes on axial, sagittal, and coronal slices
- Saves an interactive HTML report to:
  `reports/report_sample_ct.html`

---

## ✅ Sample Output

Console output (detection):

```
[12:52:13] STEP 1: Loading images ...
CT array shape: (481, 650, 529)
voxel intensity range: -4734.0 to 31743.0
Z-axis bounds: 38 to 443
Y-axis bounds: 52 to 598
X-axis bounds: 42 to 487

[12:52:15] STEP 2: Performing skull stripping on MR using FSL BET ...
Skull-stripped MR image saved at: /data/processed_scans/sample_mr_bet.nii.gz
Brain mask saved at: /data/processed_scans/sample_mr_bet_mask.nii.gz

[12:52:31] STEP 3: Loading the generated MR brain mask and applying it to the CT scan ...
MR brain mask loaded successfully.

[12:52:31] Dilating the brain mask by 30 voxels ...
Successfully Skull stripped the CT scan.

[12:52:52] STEP 4: Compute the centroid of electrodes ...
Detected total number of potential electrodes: 142

[12:52:53] STEP 5: Eliminate outliers from the list of potential electrodes ...
Processing electrodes:  52%|█████▏    | 74/142 [00:00<00:00, 733.90it/s]
Electrode outside margin 1: physical = (29.92, -35.9, -83.28), voxel = (339, 414, 31)
Electrode outside margin 2: physical = (-27.22, -37.28, -88.78), voxel = (196, 417, 18)
Processing electrodes: 100%|██████████| 142/142 [00:00<00:00, 375.20it/s]
Electrode outside margin 3: physical = (-27.55, -38.4, -87.82), voxel = (195, 420, 20)
Electrode outside margin 4: physical = (-27.75, -38.8, -87.42), voxel = (195, 421, 21)
Electrode outside margin 5: physical = (-25.96, -38.0, -88.62), voxel = (199, 419, 18)
Electrode outside margin 6: physical = (-26.36, -38.4, -88.22), voxel = (198, 420, 19)
Electrode outside margin 7: physical = (26.76, -35.6, -83.43), voxel = (331, 413, 31)
Final electrode count after eliminating 7 potential outliers: 135

[12:52:53] STEP 6: Saving electrode coordinates to the disk ...
Electrode coordinates successfully saved to: processed_scans/electrodes_sample_ct.json
```

Console output (visualization):

```
Generating report: 100%|██████████| 135/135 [00:26<00:00,  5.01it/s]
HTML report saved to: reports/report_sample_ct.html
```

Report preview (example images):
![image](https://github.com/user-attachments/assets/954b730e-2908-459a-a50a-866afb929b4a)
![image](https://github.com/user-attachments/assets/3378717c-9869-478a-8605-eb104c03f77d)
![image](https://github.com/user-attachments/assets/0b0b9a19-ac1b-424c-92d9-dc84b9af14c2)
![image](https://github.com/user-attachments/assets/497c39ef-a013-436c-9863-024e2e84ce6f)
![image](https://github.com/user-attachments/assets/c462fc1e-0316-4352-aa23-1888e7fd864d)

---

## 📂 Project Structure

```
ElecMap/
├── src/
|   └── elecmap/
│       ├── __init__.py
│       ├── electrode_detection.py
│       └── electrode_visualization.py
├── examples/
│   └── run_elecmap_demo.py
├── processed_scans/
│   └── (auto-generated outputs)
├── reports/
│   └── (auto-generated reports)
├── pyproject.toml
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 📋 JSON Output Format

The output JSON contains a list of detected electrode centroids:

```json
[
  {
    "physical_mm": [51.74, -40.14, -2.88],
    "voxel_coords": [394, 324, 250]
  },
  ...
]
```

- `physical_mm`: electrode location in real-world space (millimeters)
- `voxel_coords`: electrode position in image voxel space (indices)

---

## 🔬 Use Cases

- Epilepsy and tumor surgery planning
- Post-operative SEEG or ECoG contact localization
- Research in brain-computer interfaces (BCIs)
- Electrode tracking across imaging sessions
- Quality control of electrode placement

---

## 🧪 Dependencies

- Python 3.8+
- Python libraries:
  - `SimpleITK`
  - `matplotlib`
  - `numpy`
  - `termcolor`
  - `tqdm`
  - `nipype` (for FSL integration)

- System dependency:
  - [FSL](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation)

Install all Python dependencies with:

```bash
pip install -r requirements.txt
```

> ⚠️ Without FSL, only CT-based detection is performed. A warning will be printed.

---

## 🧾 License

This project is licensed under the [MIT License](LICENSE).

---

## 🤝 Contributing

Feedback and contributions are welcome!  
Please [open an issue](https://github.com/saberm2837/ElecMap/issues) to report bugs, request features, or contribute code.

---

## 📫 Contact

**Created by:** Mohammad Saber  
📧 Email: [mohammadsaber@gmail.com](mailto:mohammadsaber@gmail.com)  
🌐 GitHub: [https://github.com/saberm2837/ElecMap](https://github.com/saberm2837/ElecMap)

---

## 📚 Citation

If you use **ElecMap** in your research, please cite:

```bibtex
@software{ElecMap2025,
  author = {Mohammad Saber},
  title = {ElecMap: Intracranial Electrode Localization Toolkit},
  year = {2025},
  url = {https://github.com/saberm2837/ElecMap}
}
```
