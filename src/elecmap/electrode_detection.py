from concurrent.futures import ThreadPoolExecutor
from nipype.interfaces.fsl import BET
from termcolor import colored
import SimpleITK as sitk
from typing import Union
from pathlib import Path
from tqdm import tqdm
import numpy as np
import datetime
import json
import os
import sys

# Default values
SS_FRAC = 0.25
SS_MASK_DILATE = 30
BOX_MARGIN = 0.08
CUTOFF_INTENSITY = 9500
DIST_THRESHOLD = 5

def _log_msg(message):
    """Prints a message with a timestamp."""
    print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}")
    
def _vox_dist(point1: Union[list,np.ndarray], point2: Union[list,np.ndarray]) -> float:
    """
    Calculates the Euclidean distance between two 3D points using NumPy.

    Parameters:
        point1: A NumPy array or list representing the first point (x1, y1, z1).
        point2: A NumPy array or list representing the second point (x2, y2, z2).

    Returns:
        The distance between the two points.
    """
    p1 = np.array(point1)
    p2 = np.array(point2)
    return np.linalg.norm(p2 - p1)

def _find_nearest_elec_dist(vox, elec_list):
    """
    Find the nearest electrode distance from a list of electrodes.

    Parameters:
        vox(int,int,int): 3D coordinate
        elec_list: a list of 3D coordinates

    Returns:
        A tuple containing:
        - The nearest electrode distance (float).
        - The voxel coordinates of the nearest electrode (tuple).
        Returns (-1, None) if the elec_list is empty.
    """
    if not elec_list:
        return -1, None
    
    with ThreadPoolExecutor() as executor:
        distances = list(executor.map(lambda e: _vox_dist(vox, e), elec_list))
    min_idx = np.argmin(distances)
    return distances[min_idx], elec_list[min_idx]

def detect_electrodes(
    ct_file_path: str,
    mr_file_path: str,
    output_dir: str = 'processed_scans',
    ss_frac: float = SS_FRAC,
    dilate_n_voxels: int = SS_MASK_DILATE,
    margin: float = BOX_MARGIN,
    cut_off_intensity: int = CUTOFF_INTENSITY
) -> Union[str, None]:
    """
    Processes CT and MR scans to detect and localize electrodes.

    Parameters:
        ct_file_path (str): Path to the input CT NIfTI file.
        mr_file_path (str): Path to the input MR NIfTI file.
        output_dir (str, optional): Directory to save processed files. Defaults to 'processed_scans'.
        ss_frac (float, optional): Fractional intensity threshold for FSL BET (0-1). Lower values create bigger masks. Defaults to 0.25.
        dilate_n_voxels (int, optional): Number of voxels to dilate the binary mask. Defaults to 30.
        margin (float, optional): Margin (0-1) to discard slices from all three directions to avoid artifacts. Defaults to 0.08.
        cut_off_intensity (int, optional): Lower intensity threshold for electrode detection. Defaults to 9500.

    Returns:
        str: Path to the generated JSON file containing electrode coordinates, or None if an error occurs.
    """
    # Validation for input parameters
    if not 0 < ss_frac < 1:
        print("ss_frac must be between 0 and 1")
        print("Setting this parameter to default")
        ss_frac = SS_FRAC 
    if not 0 <= margin <= 0.5:
        print("Margin must be between 0 and 0.5")
        print("Setting this parameter to default")
        margin = BOX_MARGIN
    
    # Check for FSL dependency at the beginning of the function
    fsl_dir = True 
    if 'FSLDIR' not in os.environ:
        fsl_dir = False
        print(colored("\nWARNING: FSLDIR environment variable is not set.", "yellow"))
        print("-------------------------------------------------------------------------------------------")
        print("Please ensure 'FSLDIR' environment variable is correctly configured for better performance.")
        print("Continue the process without skull-stripping.")
        print("-------------------------------------------------------------------------------------------")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Load the Image
    _log_msg("STEP 1: Loading images ...")
    try:
        ct_image = sitk.ReadImage(ct_file_path)
        mr_image = sitk.ReadImage(mr_file_path)
    except Exception as e:
        print(f"Error loading images: {e}")
        return None

    ct_array = sitk.GetArrayFromImage(ct_image)
    shape_z, shape_y, shape_x = ct_array.shape
    print("CT array shape:", ct_array.shape)
    print("voxel intensity range:", np.min(ct_array), "to", np.max(ct_array))

    if np.max(ct_array) < cut_off_intensity or np.min(ct_array) > cut_off_intensity:
        print(colored("\nWARNING: Image Intensity Issue Detected!", "yellow"))
        print("-----------------------------------------------------------------------------------")
        print(f"The expected cut-off intensity ({cut_off_intensity}) for detecting electrodes should fall within ")
        print(f"the range of the lowest ({np.min(ct_array)}) to the highest ({np.max(ct_array)}) image intensity")
        print("Please try again with a different cut-off intensity!")
        print("-----------------------------------------------------------------------------------\n")
        return None
        
    # Calculate the box margin
    z_min, z_max = (round(ct_array.shape[0]*margin),round(ct_array.shape[0]*(1-margin)))
    y_min, y_max = (round(ct_array.shape[1]*margin),round(ct_array.shape[1]*(1-margin)))
    x_min, x_max = (round(ct_array.shape[2]*margin),round(ct_array.shape[2]*(1-margin)))

    print(f"Z-axis bounds: {z_min} to {z_max}")
    print(f"Y-axis bounds: {y_min} to {y_max}")
    print(f"X-axis bounds: {x_min} to {x_max}")

    # Step 2: Perform Skull Stripping on MR using FSL BET
    if fsl_dir:
        _log_msg("STEP 2: Performing skull stripping on MR using FSL BET ...")
        skullstrip = BET()
        skullstrip.inputs.in_file = mr_file_path
        skullstrip.inputs.frac = ss_frac
        skullstrip.inputs.mask = True
    
        mr_filename = Path(mr_file_path).stem
        bet_stripped_mr_file = output_dir / f'{mr_filename}_bet.nii.gz'
        skullstrip.inputs.out_file = bet_stripped_mr_file
        skullstrip_failed = False # default
    
        try:
            res = skullstrip.run()
            print(f"Skull-stripped MR image saved at: {res.outputs.out_file}")
            bet_mask_file = res.outputs.mask_file
            print(f"Brain mask saved at: {bet_mask_file}")
        except Exception as e:
            print(f"An error occurred during skull stripping: {e}")
            print("Proceeding with original CT image (no skull stripping)...")
            masked_ct_image = ct_image
            skullstrip_failed = True
    
        # Step 3: Load the generated MR Brain Mask
        if not skullstrip_failed:
            _log_msg("STEP 3: Loading the generated MR brain mask and applying it to the CT scan ...")
            try:
                mr_brain_mask = sitk.ReadImage(bet_mask_file)
                print("MR brain mask loaded successfully.")
            except Exception as e:
                print(f"Error loading MR brain mask: {e}")
                return None
        
            _log_msg(f"Dilating the brain mask by {dilate_n_voxels} voxels (to cover the skull area) ...")
            dilated_mask = sitk.BinaryDilate(mr_brain_mask, (dilate_n_voxels, dilate_n_voxels, dilate_n_voxels))
        
            dilated_brain_mask = sitk.Cast(dilated_mask, ct_image.GetPixelID())
            masked_ct_image = ct_image * dilated_brain_mask
        
            print("Successfully Skull stripped the CT scan.")
        else: 
            print("\nSkipping STEP 3 (Applying brain mask to CT scan) ...")
    else:
        print("\nSkipping STEP 2 (Skull-stripping MR scan) ...")
        print("\nSkipping STEP 3 (Applying brain mask to the CT scan) ...")
        masked_ct_image = ct_image

    # Step 4: Compute the centroid of electrodes through image segmentation
    _log_msg("STEP 4: Compute the centroid of electrodes ...")
    upper = float(sitk.GetArrayViewFromImage(ct_image).max())
    lower = cut_off_intensity
    electrode_seg = sitk.BinaryThreshold(masked_ct_image, lowerThreshold=lower, upperThreshold=upper, insideValue=1, outsideValue=0)

    cc = sitk.ConnectedComponent(electrode_seg)
    relabeled = sitk.RelabelComponent(cc, sortByObjectSize=True)

    stats = sitk.LabelShapeStatisticsImageFilter()
    stats.Execute(relabeled)

    phys_centroids = []
    voxel_centroids = []

    print(f"Detected total number of potential electrodes: {len(stats.GetLabels())}")
    
    # Step 5: Eliminate outliers from the list of potential electrodes
    _log_msg("STEP 5: Eliminate outliers from the list of potential electrodes ...")
    dup_count = 0
    out_mask_bound = 0
    
    for label in tqdm(stats.GetLabels(), desc="Processing electrodes"):
        centroid_phys = tuple(round(coord, 2) for coord in stats.GetCentroid(label))
        centroid_voxel = masked_ct_image.TransformPhysicalPointToIndex(centroid_phys)
        x, y, z = centroid_voxel
        
        nearest_elec_dist, nearest_elec = _find_nearest_elec_dist(centroid_voxel, voxel_centroids)
        if nearest_elec_dist >= 0 and nearest_elec_dist < DIST_THRESHOLD:
            dup_count += 1
            print(colored(f"Duplicate Electrode {dup_count}: physical = {centroid_phys}, voxel = {centroid_voxel}, nearest voxel = {nearest_elec}", "blue"))
        elif not (x_min <= x <= x_max and
                  y_min <= y <= y_max and
                  z_min <= z <= z_max):
            out_mask_bound += 1
            print(colored(f"Electrode outside margin {out_mask_bound}: physical = {centroid_phys}, voxel = {centroid_voxel}", "red"))
        else:
            phys_centroids.append(centroid_phys)
            voxel_centroids.append(centroid_voxel)

    print(f"Final electrode count after eliminating {dup_count+out_mask_bound} potential outliers: {len(voxel_centroids)}")

    electrode_data_for_json = []

    # Step 6: Saving electrode coordinates to the disk
    _log_msg("STEP 6: Saving electrode coordinates to the disk ...")
    for i, electrode in enumerate(range(len(voxel_centroids))):
        phy_coords = phys_centroids[electrode]
        vox_coords = voxel_centroids[electrode]

        electrode_data_for_json.append({
            "physical_mm": list(phy_coords),
            "voxel_coords": list(vox_coords)
        })
        
    ct_filename = Path(ct_file_path).stem
    json_output_file = output_dir / f'electrodes_{ct_filename}.json'

    if not electrode_data_for_json:
        print(colored("\nWARNING: No electrodes detected!","yellow"))
        return None
    
    try:
        with open(json_output_file, 'w') as f:
            json.dump(electrode_data_for_json, f, indent=4)
        print(f"Electrode coordinates successfully saved to: {json_output_file}")
        return json_output_file
    except Exception as e:
        print(f"Error saving electrode coordinates to JSON: {e}")
        return None