import matplotlib.pyplot as plt
import SimpleITK as sitk
from typing import Union
from pathlib import Path
from io import BytesIO
from tqdm import tqdm
import numpy as np
import datetime
import base64
import json


# Constants
MARKER_STYLE = dict(marker='o', markerfacecolor='none', 
                   markeredgecolor='red', markersize=6, 
                   markeredgewidth=1.5)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Electrode Localization Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .electrode {{ page-break-after: always; margin-bottom: 30px; }}
        .slice {{ display: inline-block; margin: 10px; }}
        .header {{ background-color: #f0f0f0; padding: 10px; margin-bottom: 20px; }}
        img {{ max-width: 300px; height: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Electrode Localization Report</h1>
        <p><strong>CT File:</strong> {ct_file}</p>
        <p><strong>Report Date:</strong> {date}</p>
        <p><strong>Total Detected Electrodes:</strong> {total_electrodes}</p>
    </div>
    
    {content}
</body>
</html>
"""

def _fig_to_html(fig):
    """
    Converts a Matplotlib figure to a base64-encoded HTML <img> tag.

    Parameters:
        fig (matplotlib.figure.Figure): The figure to convert.

    Returns:
        str: Base64-encoded HTML image tag.
    """
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    img_data = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f'<img src="data:image/png;base64,{img_data}">'

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

def _make_slice_plot(slice_2d: np.ndarray, marker_coords: tuple, title: str, min_intensity: float, max_intensity: float) -> plt.Figure:
    """
    Create a matplotlib plot of a 2D image slice with an overlaid electrode marker.

    Parameters:
        slice_2d (np.ndarray): The 2D image slice to display (e.g., axial, sagittal, coronal).
        marker_coords (tuple): (x, y) coordinates of the electrode marker in slice space.
        title (str): Title to display on the plot.
        min_intensity (float): Minimum display intensity for grayscale colormap.
        max_intensity (float): Maximum display intensity for grayscale colormap.
    
    Returns:
        matplotlib.figure.Figure: A matplotlib figure with the image and marker rendered.
    """    
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(slice_2d, cmap='gray', vmin=min_intensity, vmax=max_intensity)
    ax.plot(*marker_coords, **MARKER_STYLE)
    ax.set_title(title)
    ax.axis('off')
    return fig
    
def display_electrode_locations(
    ct_file_path: str,
    electrode_json_path: str,
    min_intensity: float = None,
    max_intensity: float = None,
    output_dir: str = "reports",
) -> Union[str, None]:
    """
    Generate an interactive HTML report of electrode locations. 
    The report displays axial, sagittal, and coronal slices from 
    a 3D CT volume with detected electrode locations marked.
    
    Parameters:
        ct_file_path (str): Path to CT NIfTI file
        electrode_json_path (str): Path to JSON electrode coordinates
        min_intensity (int, optional): Minimum display intensity
        max_intensity (int, optional): Maximum display intensity
        output_dir (str, optional): Output directory path

    Returns:
        str: Path to the generated HTML file containing the report, or None if an error occurs.
    """
    output_dir = Path(output_dir)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # --- Input Validation ---
    if not Path(ct_file_path).exists():
        print(f"Error: CT image file not found at {ct_file_path}")
        return None
    
    if not Path(electrode_json_path).exists():
        print(f"Error: Electrode JSON file not found at {electrode_json_path}")
        return None

    # --- Load CT Image ---
    try:
        ct_image = sitk.ReadImage(ct_file_path)
    except Exception as e:
        print(f"Error loading CT image for visualization: {e}")
        return None

    # --- Load Electrode Data from JSON ---
    try:
        with open(electrode_json_path, 'r') as f:
            electrode_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from '{electrode_json_path}': {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while reading the JSON file: {e}")
        return None

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
        return None
    
    # --- Prepare Display Array ---
    display_array = _get_display_array(ct_image)

    if min_intensity is None:
        min_intensity = np.min(display_array)
    if max_intensity is None:
        max_intensity = np.max(display_array)

    # Get original image dimensions for index transformation
    ct_image_size = ct_image.GetSize() # (X, Y, Z)
  
    # Generate HTML content
    html_content = []   
    for idx, vox_coords in enumerate(tqdm(voxel_centroids, desc="Generating report")):        
        # Transform to display coordinates
        display_X = (ct_image_size[0] - 1) - vox_coords[0] 
        display_Y = (ct_image_size[1] - 1) - vox_coords[1]
        display_Z = (ct_image_size[2] - 1) - vox_coords[2]

        # Axial slice
        fig1 = _make_slice_plot(display_array[display_Z, :, :], (display_X, display_Y),
                        f'Axial Slice: {vox_coords[2]}', min_intensity, max_intensity)
        
        # Sagittal slice
        fig2 = _make_slice_plot(display_array[:, :, display_X], (display_Y, display_Z),
                        f'Sagittal Slice: {display_X}', min_intensity, max_intensity)
        
        # Coronal slice
        fig3 = _make_slice_plot(display_array[:, display_Y, :], (display_X, display_Z),
                        f'Coronal Slice: {display_Y}', min_intensity, max_intensity)

        # Add figures to HTML
        electrode_html = f"""
        <div class="electrode">
            <h2>Electrode {idx+1}</h2>
            <p><strong>Physical:</strong> {phys_centroids[idx]} mm</p>
            <p><strong>Voxel:</strong> {voxel_centroids[idx]}</p>
            <div class="slice">{_fig_to_html(fig1)}</div>
            <div class="slice">{_fig_to_html(fig2)}</div>
            <div class="slice">{_fig_to_html(fig3)}</div>
        </div>
        """
        html_content.append(electrode_html)

    # Save the HTML file
    ct_filename = Path(ct_file_path).stem
    html_path = output_dir / f"report_{ct_filename}.html"
    with open(html_path, 'w') as f:
        f.write(HTML_TEMPLATE.format(
            ct_file=ct_file_path,
            date=datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
            total_electrodes=len(voxel_centroids),
            content='\n'.join(html_content)
        ))
        
    print(f'HTML report saved to:{html_path}')
    return str(html_path)