import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "Crytus.DICOM.Node",
    async beforeRegisterNodeDef(nodeType, nodeData, appInstance) {
        if (nodeData.name === "LoadDICOM") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                onNodeCreated?.apply(this, arguments);
                const node = this;

                // Store preview image
                node._previewImage = null;
                node._previewLoading = false;

                // --- Select File Button ---
                node.addWidget("button", "Select File", "select_file", async () => {
                    try {
                        const response = await api.fetchApi("/crytus/open_file_dialog", {
                            method: "POST",
                        });
                        if (response.status === 200) {
                            const data = await response.json();
                            if (data.path) {
                                const pathWidget = node.widgets.find((w) => w.name === "path");
                                if (pathWidget) {
                                    pathWidget.value = data.path;
                                    app.graph.setDirtyCanvas(true);
                                }
                                await loadPreview(node, data.path);
                            }
                        }
                    } catch (error) {
                        console.error("Crytus: Fetch error:", error);
                        alert("Could not open file dialog: " + error.message);
                    }
                });

                // --- Preview Widget (custom draw) ---
                const previewWidget = {
                    type: "custom",
                    name: "preview",
                    draw(ctx, theNode, widget_width, y, widget_height) {
                        if (theNode._previewImage) {
                            const img = theNode._previewImage;
                            const maxW = widget_width - 20;
                            const maxH = 200;
                            const scale = Math.min(maxW / img.width, maxH / img.height, 1);
                            const drawW = img.width * scale;
                            const drawH = img.height * scale;
                            const offsetX = (widget_width - drawW) / 2;
                            ctx.drawImage(img, offsetX, y + 5, drawW, drawH);
                        } else if (theNode._previewLoading) {
                            ctx.fillStyle = "#888";
                            ctx.font = "12px sans-serif";
                            ctx.textAlign = "center";
                            ctx.fillText("Loading preview...", widget_width / 2, y + 20);
                        } else {
                            ctx.fillStyle = "#555";
                            ctx.font = "11px sans-serif";
                            ctx.textAlign = "center";
                            ctx.fillText("No preview", widget_width / 2, y + 20);
                        }
                    },
                    computeSize() {
                        if (node._previewImage) {
                            const img = node._previewImage;
                            const maxW = 200;
                            const maxH = 200;
                            const scale = Math.min(maxW / img.width, maxH / img.height, 1);
                            return [200, img.height * scale + 10];
                        }
                        return [200, 30];
                    },
                    serializeValue() {
                        return undefined;
                    },
                };
                node.addCustomWidget(previewWidget);

                // --- Drag & Drop ---
                node.onDragOver = function (e) {
                    e.preventDefault();
                    return true;
                };
                node.onDragDrop = async function (e) {
                    e.preventDefault();

                    // Check for file path in text (e.g. from file manager drag)
                    const textData = e.dataTransfer.getData("text/plain");
                    if (textData && (textData.endsWith(".dcm") || textData.endsWith(".dicom") || textData.includes("\\"))) {
                        const pathWidget = node.widgets.find((w) => w.name === "path");
                        if (pathWidget) {
                            pathWidget.value = textData.trim();
                            app.graph.setDirtyCanvas(true);
                        }
                        await loadPreview(node, textData.trim());
                        return true;
                    }

                    // Check for dropped files
                    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                        const file = e.dataTransfer.files[0];
                        try {
                            const formData = new FormData();
                            formData.append("file", file);
                            const response = await api.fetchApi("/crytus/upload_dicom", {
                                method: "POST",
                                body: formData,
                            });
                            if (response.status === 200) {
                                const data = await response.json();
                                if (data.path) {
                                    const pathWidget = node.widgets.find((w) => w.name === "path");
                                    if (pathWidget) {
                                        pathWidget.value = data.path;
                                        app.graph.setDirtyCanvas(true);
                                    }
                                    await loadPreview(node, data.path);
                                }
                            }
                        } catch (error) {
                            console.error("Crytus: Upload error:", error);
                        }
                        return true;
                    }
                    return false;
                };

                // --- Auto-preview if path already set ---
                const origOnConfigure = node.onConfigure;
                node.onConfigure = function (info) {
                    origOnConfigure?.apply(this, arguments);
                    const pathWidget = node.widgets.find((w) => w.name === "path");
                    if (pathWidget && pathWidget.value) {
                        loadPreview(node, pathWidget.value);
                    }
                };
            };
        }
    },
});

// -- Helper: load preview from server --
async function loadPreview(node, filePath) {
    if (!filePath) return;
    node._previewLoading = true;
    node._previewImage = null;
    app.graph.setDirtyCanvas(true);

    try {
        const response = await api.fetchApi("/crytus/preview_dicom", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ path: filePath }),
        });
        if (response.status === 200) {
            const data = await response.json();
            if (data.image) {
                const img = new Image();
                img.onload = () => {
                    node._previewImage = img;
                    node._previewLoading = false;
                    node.setSize(node.computeSize());
                    app.graph.setDirtyCanvas(true);
                };
                img.onerror = () => {
                    node._previewLoading = false;
                    app.graph.setDirtyCanvas(true);
                };
                img.src = "data:image/png;base64," + data.image;
            }
        } else {
            node._previewLoading = false;
            app.graph.setDirtyCanvas(true);
        }
    } catch (e) {
        console.error("Crytus: Preview error:", e);
        node._previewLoading = false;
        app.graph.setDirtyCanvas(true);
    }
}
