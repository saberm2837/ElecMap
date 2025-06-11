from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from .utils import log_msg
import SimpleITK as sitk
import numpy as np
import datetime
import json
import os
import io

def _get_display_array(sitk_image):
    """
    Converts a SimpleITK image to a NumPy array and applies necessary flips
    to prepare it for consistent display across axial, sagittal, and coronal views.

    Parameters:
        sitk_image (SimpleITK.Image): The input 3D SimpleITK image.

    Returns:
        np.ndarray: The 3D NumPy array of the image, prepared for display.
    """
    img_array = sitk.GetArrayFromImage(sitk_image)

    # Flip to display as radiological convention: Z (I-S), Y (P-A), X (L-R)
    display_array = np.flip(img_array, axis=0)  # Flip Z (for I-S)
    display_array = np.flip(display_array, axis=1)  # Flip Y (for P-A)
    display_array = np.flip(display_array, axis=2)  # Flip X (for L-R)

    return display_array

def display_electrode_locations(
    ct_file_path: str,
    electrode_json_path: str, 
    min_intensity: int = None,
    max_intensity: int = None,
    output_dir: str = 'reports',
) -> None:
    """
    Displays axial, sagittal, and coronal slices from a 3D CT volume
    with detected electrode locations marked. Each electrode is displayed
    in a separate set of plots.

    Parameters:
        ct_file_path (str): The path to the CT NIfTI file.
        electrode_json_path (str): The path to the JSON file containing electrode coordinates.
                                   Expected format: [{"physical_mm": [...], "voxel_coords": [...]}, ...]
        min_intensity (int, optional): Minimum intensity for displaying images.
                                       If None, uses the minimum of the CT array.
        max_intensity (int, optional): Maximum intensity for displaying images.
                                       If None, uses the maximum of the CT array.
        output_dir (str, optional): Directory to save the report. Defaults to 'reports'. All automatically 
                                    identified electrode locations will be saved in a single PDF file at this path.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # --- Input Validation ---
    if not os.path.exists(ct_file_path):
        print(f"Error: CT image file not found at {ct_file_path}")
        return
    
    if not os.path.exists(electrode_json_path):
        print(f"Error: Electrode JSON file not found at {electrode_json_path}")
        return

    log_msg("STEP 1: Loading image and electrode data ...")
    # --- Load CT Image ---
    try:
        ct_image = sitk.ReadImage(ct_file_path)
        print(f"CT image loaded from {ct_file_path} for visualization.")
    except Exception as e:
        print(f"Error loading CT image for visualization: {e}")
        return

    # --- Load Electrode Data from JSON ---
    try:
        with open(electrode_json_path, 'r') as f:
            electrode_data = json.load(f)
        print(f"Electrode data loaded from {electrode_json_path}.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from '{electrode_json_path}': {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred while reading the JSON file: {e}")
        return

    # Extract physical and voxel coordinates, ensuring they are tuples
    phys_centroids = []
    voxel_centroids = []
    for entry in electrode_data:
        if 'voxel_coords' in entry and isinstance(entry['voxel_coords'], list):
            phys_centroids.append(tuple(float(coord) for coord in entry['physical_mm']))
            voxel_centroids.append(tuple(int(coord) for coord in entry['voxel_coords']))
        else:
            print(f"Warning: Skipping an electrode entry in JSON missing 'voxel_coords' or with incorrect format: {entry}")

    if not voxel_centroids:
        print("No valid electrode voxel coordinates found in the JSON file for visualization.")
        return

    # --- Prepare Display Array ---
    display_array = _get_display_array(ct_image)

    if min_intensity is None:
        min_intensity = np.min(display_array)
    if max_intensity is None:
        max_intensity = np.max(display_array)

    # Get original image dimensions for index transformation
    ct_image_size = ct_image.GetSize() # (X, Y, Z)

    log_msg("STEP 2: Generating report from identified electrode locations in the CT scan ...")
    print(f"A total of {len(voxel_centroids)} electrodes were detected. This may take some time to plot all locations.")
    ct_filename = os.path.splitext(os.path.basename(ct_file_path))[0]
    pdf_path = os.path.join(output_dir if output_dir else "reports", f"report_{ct_filename}.pdf")

    try:
        pdf = PdfPages(pdf_path)
        fig_heading = plt.figure(figsize=(15, 6)) 
        fig_heading.text(0.5, 0.8, "Electrode Localization Report",
                             fontsize=24, ha='center', va='center', wrap=True)
        fig_heading.text(0.5, 0.6, f"CT filename: {ct_file_path}", fontsize=18, ha='center', va='center')
        fig_heading.text(0.5, 0.5, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}", fontsize=18, ha='center', va='center') 

        pdf.savefig(fig_heading)
        plt.close(fig_heading)
    except Exception as e:
        print(f"Error opening PDF file for writing: {e}. Reverting to interactive display.")
        pdf = None # Disable PDF saving if error      
    
    for i, vox_coords in enumerate(voxel_centroids):
        # The text to add to the top of each electrode plot
        electrode_info_text = (
            f"Electrode {i+1}:\n"
            f"  Physical (mm) = {phys_centroids[i]}\n"
            f"  Voxel Coords = {voxel_centroids[i]}"
        )

        # Transform these original indices to indices in the `display_array`
        # which has been flipped along Z, Y, and X.
        display_X = (ct_image_size[0] - 1) - vox_coords[0] 
        display_Y = (ct_image_size[1] - 1) - vox_coords[1]
        display_Z = (ct_image_size[2] - 1) - vox_coords[2]
    
        fig, axes = plt.subplots(1, 3, figsize=(15, 6))

        # Add the text to the top of the figure for each electrode
        fig.suptitle(electrode_info_text, fontsize=12, y=0.98, ha='center', va='top')

        # Axial slice: We slice at `display_Z` from `display_array` (Z, Y, X). . 
        ax_img = display_array[display_Z, :, :]
        axes[0].imshow(ax_img, cmap='gray', vmin=min_intensity, vmax=max_intensity)
        axes[0].plot(display_X, display_Y, 'ro', fillstyle='none', markersize=5, markeredgewidth=1.5)
        axes[0].set_title(f'AFNI Axial Slice: {vox_coords[2]}')
        axes[0].axis('off')
    
        # Sagittal slice: We slice at `display_X` from `display_array` (Z, Y, X).
        sag_img = display_array[:, :, display_X]
        axes[1].imshow(sag_img, cmap='gray', vmin=min_intensity, vmax=max_intensity)
        axes[1].plot(display_Y, display_Z, 'ro', fillstyle='none', markersize=5, markeredgewidth=1.5)
        axes[1].set_title(f'AFNI Sagittal Slice: {display_X}')
        axes[1].axis('off')
    
        # Coronal slice: We slice at `display_Y` from `display_array` (Z, Y, X).
        cor_img = display_array[:, display_Y, :]
        axes[2].imshow(cor_img, cmap='gray', vmin=min_intensity, vmax=max_intensity)
        axes[2].plot(display_X, display_Z, 'ro', fillstyle='none', markersize=5, markeredgewidth=1.5)
        axes[2].set_title(f'AFNI Coronal Slice: {display_Y}')
        axes[2].axis('off')

        plt.tight_layout(rect=[0, 0, 1, 0.95]) # Adjust layout to make space for suptitle

        # --- Save to PDF or Show ---
        if pdf:
            pdf.savefig(fig, dpi=300)
        else:
            plt.show()
                
        plt.close(fig) # Close the figure to free up memory immediately   

    log_msg("STEP 3: Finalizing electrode localization plots ...")
    if pdf:
        pdf.close()
        print(f"All electrode localization plots successfully saved to {pdf_path}")

