from nipype.interfaces.fsl import BET
from termcolor import colored
from .utils import log_msg
import SimpleITK as sitk
import numpy as np
import datetime
import json
import os

def _vox_dist(point1: list|np.ndarray, point2: list|np.ndarray) -> float:
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
    min_dist = float('inf')  # Initialize with a high value
    min_dist_vox = None
    if not elec_list:
        return -1, None
    else:
        for elec in elec_list:
            dist = _vox_dist(vox, elec)
            if dist < min_dist:
                min_dist = dist
                min_dist_vox = elec
        return min_dist, min_dist_vox

def detect_electrodes(
    ct_file_path: str,
    mr_file_path: str,
    output_dir: str = 'processed_scans',
    ss_frac: float = 0.25,
    dilate_n_voxels: int = 30,
    margin: float = 0.08,
    cut_off_intensity: int = 9500,
    fsl_dir: str = '/opt/fsl'
) -> None:
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
        fsl_dir (str, optional): Path to FSL installation directory. Defaults to '/opt/fsl'.

    Returns:
        str: Path to the generated JSON file containing electrode coordinates, or None if an error occurs.
    """

    os.makedirs(output_dir, exist_ok=True)
    if 'FSLDIR' not in os.environ:
        os.environ['FSLDIR'] = fsl_dir

    # Step 1: Load the Image
    log_msg("STEP 1: Loading images...")
    try:
        ct_image = sitk.ReadImage(ct_file_path)
        mr_image = sitk.ReadImage(mr_file_path)
        print("Images loaded successfully.")
    except Exception as e:
        print(f"Error loading images: {e}")
        return None

    ct_array = sitk.GetArrayFromImage(ct_image)
    shape_z, shape_y, shape_x = ct_array.shape
    print("CT array shape:", ct_array.shape)
    print("voxel intensity range:", np.min(ct_array), "to", np.max(ct_array))

    if np.max(ct_array) < cut_off_intensity:
        print(colored("\nWARNING: Image Intensity Issue Detected!", "yellow"))
        print("--------------------------------------------------")
        print(f"The highest intensity ({np.max(ct_array)}) of this image is lower than "
              f"the expected cut-off intensity ({cut_off_intensity}) for electrode detection.")
        print("Suggestion: This might indicate a low-quality CT scan or unusual intensity scaling.")
        print("            Consider lowering the electrode detection threshold ('cut_off_intensity').")
        print("Disclaimer: Performance is not guaranteed for low-quality images. You may encounter false positives or miss electrodes.")
        print("--------------------------------------------------\n")

    # Calculate the box margin 
    z_min, z_max = (round(ct_array.shape[0]*margin),round(ct_array.shape[0]*(1-margin)))
    y_min, y_max = (round(ct_array.shape[1]*margin),round(ct_array.shape[1]*(1-margin)))
    x_min, x_max = (round(ct_array.shape[2]*margin),round(ct_array.shape[2]*(1-margin)))

    print(f"Z-axis bounds: {z_min} to {z_max}")
    print(f"Y-axis bounds: {y_min} to {y_max}")
    print(f"X-axis bounds: {x_min} to {x_max}")

    # Step 2: Perform Skull Stripping on MR using FSL BET
    log_msg("STEP 2: Performing skull stripping on MR using FSL BET...")
    skullstrip = BET()
    skullstrip.inputs.in_file = mr_file_path
    skullstrip.inputs.frac = ss_frac
    skullstrip.inputs.mask = True

    mr_filename = os.path.splitext(os.path.basename(mr_file_path))[0]
    bet_stripped_mr_file = os.path.join(output_dir, f'{mr_filename}_bet.nii.gz')
    skullstrip.inputs.out_file = bet_stripped_mr_file

    try:
        res = skullstrip.run()
        print("Skull stripping complete.")
        print(f"Skull-stripped MR image saved at: {res.outputs.out_file}")
        bet_mask_file = res.outputs.mask_file
        print(f"Brain mask saved at: {bet_mask_file}")
    except Exception as e:
        print(f"An error occurred during skull stripping: {e}")
        return None

    # Step 3: Load the generated MR Brain Mask
    log_msg("STEP 3: Loading the generated MR brain mask and applying it to the CT scan...")
    try:
        mr_brain_mask = sitk.ReadImage(bet_mask_file)
        print("MR brain mask loaded successfully.")
    except Exception as e:
        print(f"Error loading MR brain mask: {e}")
        return None

    log_msg(f"Dilating the brain mask by {dilate_n_voxels} voxels...")
    dilated_mask = sitk.BinaryDilate(mr_brain_mask, (dilate_n_voxels, dilate_n_voxels, dilate_n_voxels))

    dilated_brain_mask = sitk.Cast(dilated_mask, ct_image.GetPixelID())
    masked_ct_image = ct_image * dilated_brain_mask

    print("Successfully Skull stripped the CT scan.")

    # Step 4: Compute the centroid of electrodes through image segmentation
    log_msg("STEP 4: Compute the centroid of electrodes...")
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
    log_msg("STEP 5: Eliminate outliers from the list of potential electrodes...")
    dup_count = 0
    out_mask_bound = 0
    for label in stats.GetLabels():
        centroid_phys = tuple(round(coord, 2) for coord in stats.GetCentroid(label))
        centroid_voxel = masked_ct_image.TransformPhysicalPointToIndex(centroid_phys)

        nearest_elec_dist, nearest_elec = _find_nearest_elec_dist(centroid_voxel, voxel_centroids)
        if nearest_elec_dist >= 0 and nearest_elec_dist < 5:
            dup_count += 1
            print(colored(f"Duplicate Electrode {dup_count}: physical = {centroid_phys}, voxel = {centroid_voxel}, nearest voxel = {nearest_elec}", "blue"))
        elif not (x_min <= centroid_voxel[0] <= x_max and
                  y_min <= centroid_voxel[1] <= y_max and
                  z_min <= centroid_voxel[2] <= z_max):
            out_mask_bound += 1
            print(colored(f"Electrode outside margin {out_mask_bound}: physical = {centroid_phys}, voxel = {centroid_voxel}", "red"))
        else:
            phys_centroids.append(centroid_phys)
            voxel_centroids.append(centroid_voxel)

    print(f"Final electrode count after eliminating {dup_count+out_mask_bound} potential outliers: {len(voxel_centroids)}")

    electrode_data_for_json = []

    # Step 6: Saving electrode coordinates to the disk
    log_msg("STEP 6: Saving electrode coordinates to the disk...")
    for i, electrode in enumerate(range(len(voxel_centroids))):
        phy_coords = phys_centroids[electrode]
        vox_coords = voxel_centroids[electrode]

        electrode_data_for_json.append({
            "physical_mm": list(phy_coords),
            "voxel_coords": list(vox_coords)
        })
        
    ct_filename = os.path.splitext(os.path.basename(ct_file_path))[0]
    json_output_file = os.path.join(output_dir, f'electrodes_{ct_filename}.json')

    try:
        with open(json_output_file, 'w') as f:
            json.dump(electrode_data_for_json, f, indent=4)
        print(f"Electrode coordinates successfully saved to: {json_output_file}")
        return json_output_file
    except Exception as e:
        print(f"Error saving electrode coordinates to JSON: {e}")
        return None