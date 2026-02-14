import torch
import numpy as np
import os

try:
    import pydicom
    from pydicom.pixel_data_handlers.util import apply_voi_lut
except ImportError:
    pydicom = None

class LoadDICOM:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "path": ("STRING", {"default": "", "multiline": False}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_dicom"
    CATEGORY = "Crytus/Input"

    def load_dicom(self, path):
        if pydicom is None:
            raise ImportError("pydicom is not installed. Please install it using 'pip install pydicom'")

        if not path:
            raise ValueError("No file path specified. Please use the 'Select File' button or enter a path manually.")

        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        try:
            dcm = pydicom.dcmread(path)
            
            # Helper function to apply VOI LUT or windowing
            if 'VOILUTSequence' in dcm or 'WindowCenter' in dcm:
                pixel_array = apply_voi_lut(dcm.pixel_array, dcm)
            else:
                pixel_array = dcm.pixel_array

            # Convert to float and normalize
            pixel_array = pixel_array.astype(np.float32)
            
            # Simple normalization to 0-1 range if not already
            if pixel_array.max() > 1.0:
                pixel_array = (pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min())

            # Handle dimensions
            # ComfyUI expects (Batch, Height, Width, Channels)
            if len(pixel_array.shape) == 2:
                # (H, W) -> (1, H, W, 1) -> (1, H, W, 3) for RGB consistency
                image = torch.from_numpy(pixel_array)[None, :, :, None].repeat(1, 1, 1, 3)
                mask = torch.zeros((1, pixel_array.shape[0], pixel_array.shape[1]), dtype=torch.float32)
            elif len(pixel_array.shape) == 3:
                 # (Frames, H, W) or (H, W, C) - simplistic assumption for now: if 3rd dim is 3, it's RGB
                if pixel_array.shape[2] == 3:
                     image = torch.from_numpy(pixel_array)[None, :, :, :]
                else:
                    # Treat as grayscale frames: (D, H, W) -> (D, H, W, 3)
                    image = torch.from_numpy(pixel_array)[:, :, :, None].repeat(1, 1, 1, 3)
                mask = torch.zeros((image.shape[0], image.shape[1], image.shape[2]), dtype=torch.float32)
            else:
                raise ValueError(f"Unsupported DICOM shape: {pixel_array.shape}")

            return (image, mask)

        except Exception as e:
            raise RuntimeError(f"Error loading DICOM file: {e}")

    @classmethod
    def IS_CHANGED(s, path):
        if not path:
            return float("NaN")
        return path

NODE_CLASS_MAPPINGS = {
    "LoadDICOM": LoadDICOM
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadDICOM": "Load DICOM"
}
