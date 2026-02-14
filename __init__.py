from .concatenator import NODE_CLASS_MAPPINGS as CONCAT_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as CONCAT_DISPLAY_MAPPINGS
from .dicom_nodes import NODE_CLASS_MAPPINGS as DICOM_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as DICOM_DISPLAY_MAPPINGS

NODE_CLASS_MAPPINGS = {**CONCAT_MAPPINGS, **DICOM_MAPPINGS}
NODE_DISPLAY_NAME_MAPPINGS = {**CONCAT_DISPLAY_MAPPINGS, **DICOM_DISPLAY_MAPPINGS}

WEB_DIRECTORY = "./js"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

# --- API Routes ---
try:
    from server import PromptServer
    from aiohttp import web
    import asyncio
    import subprocess
    import sys
    import os
    import io
    import base64
    import numpy as np

    try:
        import pydicom
        from pydicom.pixel_data_handlers.util import apply_voi_lut
    except ImportError:
        pydicom = None

    # ---- File Dialog (PowerShell / zenity) ----
    def _open_file_dialog_sync():
        """Open a file dialog using PowerShell (Windows) or zenity (Linux)."""
        if sys.platform == "win32":
            ps_script = r'''
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Filter = "DICOM files (*.dcm;*.dicom)|*.dcm;*.dicom|All files (*.*)|*.*"
$dialog.Title = "Select DICOM File"
$dialog.Multiselect = $false
$result = $dialog.ShowDialog()
if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
    Write-Output $dialog.FileName
}
'''
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True, text=True, timeout=120
            )
            return result.stdout.strip()
        else:
            try:
                result = subprocess.run(
                    ["zenity", "--file-selection", "--title=Select DICOM File",
                     "--file-filter=DICOM files | *.dcm *.dicom", "--file-filter=All files | *"],
                    capture_output=True, text=True, timeout=120
                )
                return result.stdout.strip()
            except FileNotFoundError:
                raise RuntimeError("No GUI file dialog available.")

    @PromptServer.instance.routes.post("/crytus/open_file_dialog")
    async def open_file_dialog(request):
        try:
            loop = asyncio.get_event_loop()
            path = await loop.run_in_executor(None, _open_file_dialog_sync)
            return web.json_response({"path": path})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    # ---- DICOM Preview (returns base64 PNG) ----
    def _generate_preview(file_path, max_size=256):
        """Read DICOM and return base64-encoded PNG string."""
        if pydicom is None:
            raise ImportError("pydicom is not installed")

        dcm = pydicom.dcmread(file_path)

        if 'VOILUTSequence' in dcm or 'WindowCenter' in dcm:
            pixel_array = apply_voi_lut(dcm.pixel_array, dcm)
        else:
            pixel_array = dcm.pixel_array

        pixel_array = pixel_array.astype(np.float64)
        if pixel_array.max() > pixel_array.min():
            pixel_array = (pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min())
        pixel_array = (pixel_array * 255).astype(np.uint8)

        # Handle multi-frame: take first frame
        if len(pixel_array.shape) == 3 and pixel_array.shape[2] != 3:
            pixel_array = pixel_array[0]

        # Resize to fit max_size while keeping aspect ratio
        from PIL import Image
        if len(pixel_array.shape) == 2:
            img = Image.fromarray(pixel_array, mode='L').convert('RGB')
        else:
            img = Image.fromarray(pixel_array, mode='RGB')

        img.thumbnail((max_size, max_size), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

    @PromptServer.instance.routes.post("/crytus/preview_dicom")
    async def preview_dicom(request):
        try:
            data = await request.json()
            file_path = data.get("path", "")
            if not file_path or not os.path.exists(file_path):
                return web.json_response({"error": "File not found"}, status=400)

            loop = asyncio.get_event_loop()
            b64_png = await loop.run_in_executor(None, _generate_preview, file_path)
            return web.json_response({"image": b64_png})
        except Exception as e:
            print(f"Crytus Nodes: Preview error: {e}")
            return web.json_response({"error": str(e)}, status=500)

    # ---- File Upload (for drag & drop) ----
    @PromptServer.instance.routes.post("/crytus/upload_dicom")
    async def upload_dicom(request):
        try:
            reader = await request.multipart()
            field = await reader.next()

            if field is None:
                return web.json_response({"error": "No file uploaded"}, status=400)

            filename = field.filename or "uploaded.dcm"

            # Save to a temp directory inside crytus_nodes
            upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
            os.makedirs(upload_dir, exist_ok=True)

            file_path = os.path.join(upload_dir, filename)
            with open(file_path, 'wb') as f:
                while True:
                    chunk = await field.read_chunk()
                    if not chunk:
                        break
                    f.write(chunk)

            return web.json_response({"path": file_path})
        except Exception as e:
            print(f"Crytus Nodes: Upload error: {e}")
            return web.json_response({"error": str(e)}, status=500)

except Exception as e:
    print(f"Crytus Nodes: Could not register API routes: {e}")
