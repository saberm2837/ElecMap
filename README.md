# ElecMap: Automated Electrode Detection and Visualization

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

# ElecMap

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

## 🧠 Features <a name="features"></a>

- **Automated Electrode Detection**: Identifies electrode locations in CT scans by integrating with MR skull stripping (via FSL BET) to focus the detection within the brain's vicinity.
- **Robust Outlier Elimination**: Includes logic to filter out duplicate detections and artifacts outside the expected brain region.
- **Detailed Localization Output**: Saves detected electrode physical location and voxel coordinates to a JSON file for easy programmatic access.
- **Electrode Visualization**: Provides a tool to generate multi-page PDF reports. These reports help users visually confirm each detected electrode's location across axial, sagittal, and coronal slices of the CT scan.
- **Configurable Parameters**: Allows customization of critical parameters like skull-stripping fraction, dilation voxels, and intensity thresholds for flexible application.

---

## 📦 Installation <a name="installation"></a>

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ElecMap.git
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
import ElecMap.electrode_detection as ed

# Detect electrodes using CT and MR images
ed.detect_electrodes('CT_016.nii', 'MR_016.nii')
```

- This step performs:
  - Image loading
  - Skull-stripping of the MR scan
  - Application of the MR brain mask to the CT
  - Electrode candidate detection and outlier elimination
  - Saves electrode coordinates to:  
    `processed_scans/electrodes_CT_016.json`

---

### 2. Electrode Visualization <a name="electrode-visualization"></a>

```python
import ElecMap.electrode_visualization as ev

# Visualize and generate PDF report
ev.display_electrode_locations('CT_016.nii', 'processed_scans/electrodes_CT_016.json')
```

- Outputs a PDF report in the current directory:  
  `./report_CT_016.pdf`

---

## 📂 Directory Structure <a name="project-structure"></a>

```
ElecMap/
├── electrode_detection.py
├── electrode_visualization.py
├── __init__.py
processed_scans/
├── MR_016_bet.nii.gz
├── MR_016_bet_mask.nii
├── electrodes_CT_016.json
CT_016.nii
MR_016.nii
report_CT_016.pdf
```

---

## 📋 JSON Output Format 

The JSON file `electrodes_CT_XXX.json` contains a list of electrode coordinates:

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

Sample console output:
```
[13:08:25] STEP 2: Performing skull stripping on MR using FSL BET...
Skull stripping complete.
Brain mask saved at: MR_016_bet_mask.nii
[13:09:00] STEP 4: Compute the centroid of electrodes...
Detected total number of potential electrodes: 142
Final electrode count after eliminating 7 potential outliers: 135
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

Contributions are welcome! Feel free to fork this repository and submit pull requests.

1. Fork the repo
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a pull request

---

## 📫 Contact <a name="contact"></a>

Created by Mohammad Saber.  
For questions or feedback, open an issue or email: `mohammadsaber@gmail.com`
