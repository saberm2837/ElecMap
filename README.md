# 🧠 ElecMap: Intracranial Electrode Localization Toolkit

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

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
- [Dependencies](#dependencies)
- [License](#license)
- [Contact](#contact)

## 📘 Introduction <a name="introduction"></a>

ElecMap is a Python package designed for the automated detection of intracranial electrodes from CT and MR brain scans. Its primary purpose is to accurately identify and localize electrode centroids within medical imaging data. Complementary to its core detection capability, the package also includes a visualization tool to help users review and display the detected electrode locations.

This package leverages powerful libraries such as SimpleITK for image processing, nipype for interfacing with FSL's brain extraction tool (BET), and matplotlib for generating insightful visualizations.

---

## 🌟 Key Features <a name="features"></a>

- **Precise Electrode Mapping**: Accurately localizes electrode centroids in 3D space
- **Multi-Modal Integration**: Combines CT and MR data for improved detection
- **Clinical-Grade Output**: Generates standardized PDF reports for documentation
- **Smart Filtering**: Automatic outlier rejection and duplicate detection

---

## 📦 Installation <a name="installation"></a>

1. **Clone the repository**:
   ```bash
   git clone https://github.com/saberm2837/ElecMap.git
   cd ElecMap
   ```

2. **Install dependencies** (preferably inside a virtual environment):
   ```bash
   pip install -r requirements.txt
   ```

3. **FSL Dependency**:
   Make sure [FSL](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation) is installed and accessible in your environment.
   ```bash
   export FSLDIR=/opt/fsl
   source $FSLDIR/etc/fslconf/fsl.sh
   ```

---

## 🛠️ Usage <a name="usage"></a>

### 1. Electrode Detection <a name="electrode-detection"></a>

```python
from ElecMap import detect_electrodes

# Input files
ct_file = '/path/to/your/sample_ct.nii'
mr_file = '/path/to/your/sample_mr.nii'

# Detect electrodes using CT and MR images
detect_electrodes(ct_file, mr_file)
```

- This step performs:
  1. Image loading
  2. Skull-stripping of the MR scan
  3. Application of the MR brain mask to the CT
  4. Electrode candidate detection and outlier elimination
  5. Saves electrode coordinates to:  
    `processed_scans/electrodes_sample_ct.json`

---

### 2. Electrode Visualization <a name="electrode-visualization"></a>

```python
from ElecMap import display_electrode_locations

# Input files
ct_file = '/path/to/your/sample_ct.nii'
generated_json_path = 'processed_scans/electrodes_sample_ct.json'

# Visualize and generate PDF report
display_electrode_locations(ct_file, generated_json_path)
```

- Outputs a PDF report in the current directory:  
  `./report_sample_ct.pdf`

- A part of an example PDF report is shown below:
  ![image](https://github.com/user-attachments/assets/954b730e-2908-459a-a50a-866afb929b4a)
  ![image](https://github.com/user-attachments/assets/3378717c-9869-478a-8605-eb104c03f77d)
  ![image](https://github.com/user-attachments/assets/0b0b9a19-ac1b-424c-92d9-dc84b9af14c2)
  ![image](https://github.com/user-attachments/assets/497c39ef-a013-436c-9863-024e2e84ce6f)
  ![image](https://github.com/user-attachments/assets/c462fc1e-0316-4352-aa23-1888e7fd864d)

---

## 📂 Directory Structure <a name="project-structure"></a>

```
ElecMap/
├── elecmap/
│	├── __init__.py
|   ├── electrode_detection.py
|	├── electrode_visualization.py
|	└── utils.py
|
├── examples/                 
│   └── run_elecmap_demo.py
|
├── LICENCE
├── README.md
├── requirements.txt
├── setup.py
└── pyproject.toml 
```
---

## 📋 JSON Output Format 

The JSON file `electrodes_sample_ct.json` contains a list of electrode coordinates:

```json
[
  {
    "physical_mm": [51.74, -40.14, -2.88],
    "voxel_coords": [394, 324, 250]
  },
  ...
]
```

---

## ✅ Example Output <a name="sample-output"></a>

- Sample console output from `ElecMap.electrode_detection`:
```
[10:24:39] STEP 1: Loading images...
Images loaded successfully.
CT array shape: (481, 650, 529)
voxel intensity range: -4734.0 to 31743.0
Z-axis bounds: 38 to 443
Y-axis bounds: 52 to 598
X-axis bounds: 42 to 487

[10:24:41] STEP 2: Performing skull stripping on MR using FSL BET...
250610-10:24:41,560 nipype.interface WARNING:
	 FSLOUTPUTTYPE environment variable is not set. Setting FSLOUTPUTTYPE=NIFTI
Skull stripping complete.
Skull-stripped MR image saved at: /path/to/your/processed_scans/sample_mr_bet.nii.gz
Brain mask saved at: /path/to/your/processed_scans/sample_mr_bet_mask.nii

[10:24:55] STEP 3: Loading the generated MR brain mask and applying it to the CT scan...
MR brain mask loaded successfully.

[10:24:55] Dilating the brain mask by 30 voxels...
Successfully Skull stripped the CT scan.

[10:25:16] STEP 4: Compute the centroid of electrodes...
Detected total number of potential electrodes: 142

[10:25:16] STEP 5: Eliminate outliers from the list of potential electrodes...
Electrode outside margin 1: physical = (29.92, -35.9, -83.28), voxel = (339, 414, 31)
Electrode outside margin 2: physical = (-27.22, -37.28, -88.78), voxel = (196, 417, 18)
Electrode outside margin 3: physical = (-27.55, -38.4, -87.82), voxel = (195, 420, 20)
Electrode outside margin 4: physical = (-27.75, -38.8, -87.42), voxel = (195, 421, 21)
Electrode outside margin 5: physical = (-25.96, -38.0, -88.62), voxel = (199, 419, 18)
Electrode outside margin 6: physical = (-26.36, -38.4, -88.22), voxel = (198, 420, 19)
Electrode outside margin 7: physical = (26.76, -35.6, -83.43), voxel = (331, 413, 31)
Final electrode count after eliminating 7 potential outliers: 135

[10:25:17] STEP 5: Saving electrode coordinates to the disk...

Electrode coordinates successfully saved to: processed_scans/electrodes_sample_ct.json
```
- Sample console output from `ElecMap.electrode_visualizaion`:
```
[10:25:17] Loading image and electrode data ...
CT image loaded from sample_ct.nii for visualization.
Electrode data loaded from processed_scans/electrodes_sample_ct.json.

[10:25:18] Generating report from identified electrode locations in the CT scan ...
A total of 135 electrodes were detected. This may take some time to plot all locations.

[10:26:22] Finalizing electrode localization plots ...

All electrode localization plots successfully saved to reports_elecmap/report_sample_ct.pdf
```

PDF preview shows axial/sagittal/coronal views with electrode markers for each contact.

---

## 🧪 Requirements <a name="dependencies"></a>

- Python 3.7+
- `SimpleITK`
- `matplotlib`
- `numpy`
- `fsl` (installed on system)
- Optional: `nibabel`, `nipype` if extending the pipeline

Install dependencies using:
```bash
pip install -r requirements.txt
```

---

## 🧾 License <a name="license"></a>

MIT License. See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing 

Feedback and bug reports are welcome! Please open an issue on [GitHub](https://github.com/saberm2837/ElecMap/issues) to discuss suggestions.

---

## 📫 Contact <a name="contact"></a>

Created by Mohammad Saber.  
For questions or feedback, open an issue or email: `mohammadsaber@gmail.com`
