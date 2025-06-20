import os
from pathlib import Path
from elecmap import electrode_detection as ed
from elecmap import electrode_visualization as ev

def main():
    # === Define Input Paths ===
    ct_path = "data/CT_016.nii"
    mr_path = "data/MR_016.nii"

    # === Make sure 'FSLDIR' and 'FSLOUTPUTTYPE' are set properly ===
    if 'FSLDIR' not in os.environ:
        os.environ['FSLDIR'] = '/opt/fsl'
        os.environ['FSLOUTPUTTYPE'] = 'NIFTI_GZ'
    
    # ---- Step 1: Detect Electrode Locations ----
    print("\nDetect Electrode Locations ...")
    ed.detect_electrodes(ct_path, mr_path)
    
    # === Construct path to JSON output ===
    ct_basename = Path(ct_path).stem
    json_output_path = f"processed_scans/electrodes_{ct_basename}.json"  # Auto-saved by detect_electrodes()

    # ---- Step 2: Visualize Electrode Locations ----
    print("\nVisualize Electrode Locations ...")
    ev.display_electrode_locations(ct_path, json_output_path)

if __name__ == "__main__":
    main()