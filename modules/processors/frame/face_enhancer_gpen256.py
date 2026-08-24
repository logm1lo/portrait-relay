"""GPEN-BFR-256 processor configured from the shared implementation."""

from modules.processors.frame._gpen_enhancer import GpenEnhancer

NAME = "PORTRAIT-RELAY.FACE-ENHANCER-GPEN256"
_processor = GpenEnhancer(NAME, 256, "GPEN-BFR-256.onnx")

pre_check = _processor.pre_check
pre_start = _processor.pre_start
get_enhancer = _processor.get_enhancer
enhance_face = _processor.enhance_face
process_frame = _processor.process_frame
process_frame_v2 = _processor.process_frame_v2
process_frames = _processor.process_frames
process_image = _processor.process_image
process_video = _processor.process_video
