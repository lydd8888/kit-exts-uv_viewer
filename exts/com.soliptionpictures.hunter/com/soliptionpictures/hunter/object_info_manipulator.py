import omni.kit.pipapi

omni.kit.pipapi.install("matplotlib==3.8.2")
omni.kit.pipapi.install("numpy==1.26.2")
omni.kit.pipapi.install("pycairo==1.25.1")

from PIL import Image, ImageDraw
from pxr import Usd,Gf,UsdGeom,Vt
from omni.ui import scene as sc
import omni.ui as ui
from omni.ui import color as cl
import carb
from omni.ui_scene._scene import Color4
import omni.usd
import matplotlib.pyplot as plt
import numpy as np
import cairo
from .uv_viewer import UvModel
import time
import os
from pathlib import Path



class ObjInfoManipulator(sc.Manipulator):
    """
    Manipulator that display the object uv right next to the object
    """
    def __init__(self, viewport_window, model,**kwargs) -> None:
        super().__init__(**kwargs)
        
        # Build Cache for the UV data
        self.cache = {}

        self.vp_win = viewport_window

        resolution = self.vp_win.viewport_api.get_texture_resolution()
        self._aspect_ratio = resolution[0] / resolution[1]
        self._width = resolution[0]
        self._height = resolution[1]

        if model is None:
            self.model = UvModel()  # Initialize with UvModel() if model is not provided
        else:
            self.model = model  # Use the provided model if it's given

        levels_to_go_up = 3
        script_directory = Path(__file__).resolve()
        script_directory = script_directory.parents[levels_to_go_up]
        #script_directory = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        uv_path = "data/output.png"
        uv_background = "data/uv_background.jpg"
        self.file_path = os.path.join(script_directory,uv_path)
        self.uv_background = os.path.join(script_directory,uv_background)
        
    def on_build(self) -> None:
        """Called when the model is changed and rebuilds the whole manipulator"""

        initial_mtime = os.path.getmtime(self.file_path)
        
        aspect_ratio = self.get_aspect_ratio()
        width = self.get_width()
        height = self.get_height()
        inverse_ratio = 1 / aspect_ratio

        # Get uv_size, by default it is 50 from model file
        uv_size = self.model.uv_size.as_float

        if not self.model:
            return
        
        # If we don't have selection then just return
        if self.model.get_item("name") == "":
            return

        # Track aspect ratio to determine where to place the uv graph
        if width>height:
            move = sc.Matrix44.get_translation_matrix(-0.9,-0.9*inverse_ratio,0)
            rotate = sc.Matrix44.get_rotation_matrix(0,0,0)
            scale = sc.Matrix44.get_scale_matrix(0.01*uv_size,0.01*uv_size,0.6)
            transform = move*rotate*scale
            with sc.Transform(transform):
                with sc.Transform(sc.Matrix44.get_translation_matrix(0.5,0.5,0)):
                    self._build_safe_rect()
                self._build_axis()
                self._build_uv()

                # Build Uv and save to disk
                time.sleep(0.15)
                current_mtime = os.path.getmtime(self.file_path)
                # Compare current modification time with the initial one
                if current_mtime != initial_mtime:
                    carb.log_warn(current_mtime)
                    carb.log_warn(initial_mtime)
                    # File has been updated, call _show_uv()
                    self._show_uv()
                    # Update the initial_mtime to the current modification time
                    initial_mtime = current_mtime

        else :
            move = sc.Matrix44.get_translation_matrix(-0.9,-0.9*inverse_ratio,0)
            rotate = sc.Matrix44.get_rotation_matrix(0,0,0)
            scale = sc.Matrix44.get_scale_matrix(0.5,0.5,0.5)
            transform = move*rotate*scale
            with sc.Transform(transform):
                with sc.Transform(sc.Matrix44.get_translation_matrix(0.5,0.5,0)):
                    self._build_safe_rect()
                self._build_axis()
                self._build_uv()
                
                # Build Uv and save to disk
                time.sleep(0.15)
                current_mtime = os.path.getmtime(self.file_path)
                # Compare current modification time with the initial one
                if current_mtime != initial_mtime:
                    carb.log_warn(current_mtime)
                    carb.log_warn(initial_mtime)
                    # File has been updated, call _show_uv()
                    self._show_uv()
                    # Update the initial_mtime to the current modification time
                    initial_mtime = current_mtime

    # Check if uv png is new
    def is_file_updated(file_path, reference_time):
        file_stat = os.stat(file_path)
        file_modification_time = time.localtime(file_stat.st_mtime)
        return file_modification_time > reference_time

    def _build_uv(self):
        # Get the object's path as a unique key
        object_path  = self.model.get_item('name')
        # Check if object information is already in the cache
        if object_path in self.cache:
            object_info = self.cache[object_path]
            carb.log_warn("uv info in cache")
        else:
            carb.log_warn("uv info not in cache")
            # Gather information
            stage = omni.usd.get_context().get_stage()
            mesh = stage.GetPrimAtPath(self.model.get_item('name'))
            if mesh == None:
                return
        
            if mesh.GetTypeName() != "Mesh":
                carb.log_error("PLEASE SELECT A MESH")
                return
            else:
                st = mesh.GetAttribute("primvars:st").Get()
                st_indices = []

                if mesh.GetAttribute("primvars:st:indices"):
                    st_indices =  mesh.GetAttribute("primvars:st:indices").Get()

                uv_coordinates = st
                vertex_indices = list(range(len(uv_coordinates)))
                vertex_counts = mesh.GetAttribute("faceVertexCounts").Get()
                
                # Create a UV Mesh with UV Faces
                if st_indices:
                    uv_mesh = np.array([uv_coordinates[i] for i in st_indices])
                else:
                    uv_mesh = np.array([uv_coordinates[i] for i in vertex_indices])

                # Initialize object_info dictionary
                object_info = {
                    "uv_mesh": uv_mesh,
                    "vertex_counts": vertex_counts,
                    # Add any other information needed for self._draw_uv_line here
                }

                # Store the object information in the cache
                self.cache[object_path] = object_info

        # Retrieve the required information from the cached object_info dictionary
        uv_mesh = object_info["uv_mesh"]
        vertex_counts = object_info["vertex_counts"]  
        
        # initial count, will plus count number in vertex_counts
        current_index = 0
        
        # for debug only
        loop_counter = 0

        width, height = 512, 512
        # image = Image.new("RGB", (width, height), (0, 0, 0))
        # draw = ImageDraw.Draw(image)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface) 
        # Set background color
        ctx.set_source_rgba(0, 0, 0, 0.8)
        ctx.paint()   

        # Set the line width for thinner lines (adjust as needed)
        line_width = 0.7  # You can change this value to make the lines thinner or thicker
        ctx.set_line_width(line_width)   

        for count in vertex_counts:
            uv_face = uv_mesh[current_index:current_index+count]
            pixel_uv_face = [(uv[0] * width, uv[1] * height) for uv in uv_face]
            ctx.set_source_rgb(0.6, 0.6, 0.6)  # Light gray outline
            ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)  # Filling rule
            ctx.move_to(*pixel_uv_face[0])
            for point in pixel_uv_face[1:]:
                ctx.line_to(*point)
            ctx.close_path()
            ctx.stroke()
            ctx.set_source_rgb(0.2, 0.2, 0.2)  # Dark gray fill
            ctx.fill()

            current_index += count
            
            # for debug only, test for loop counts
            loop_counter += 1
            if loop_counter >= 1000000:
                break

        # image.save("D:/Amazon_Box_Stable_Diffusion/HoudiniUV/UV_Viewer_Extension/kit-exts-uv_viewer/exts/com.soliptionpictures.hunter/data/output.png")
        surface.write_to_png(self.file_path)

    def _show_uv(self):
        point_count = 4
        # Form the mesh data
        alpha = 0.9
        points = [[0, 0, 0], [0, 1, 0], [1, 1, 0], [1, 0, 0]]
        vertex_indices = [0, 1, 2, 3]
        colors = [[1, 1, 1, alpha], [1, 1, 1, alpha], [1, 1, 1, alpha], [1, 1, 1, alpha]]
        uvs = [[0, 0], [0, 1], [1, 1], [1, 0]]
        # Draw the mesh
        uv_background = self.uv_background
        filename = self.file_path
        sc.TexturedMesh(uv_background, uvs, points, colors, [point_count], vertex_indices)
        sc.TexturedMesh(filename, uvs, points, colors, [point_count], vertex_indices)

    def display_previous_show_uv(self):
        aspect_ratio = self.get_aspect_ratio()
        width = self.get_width()
        height = self.get_height()
        inverse_ratio = 1 / aspect_ratio

        if width>height:
            move = sc.Matrix44.get_translation_matrix(-0.9,-0.9*inverse_ratio,0)
            rotate = sc.Matrix44.get_rotation_matrix(0,0,0)
            scale = sc.Matrix44.get_scale_matrix(0.6,0.6,0.6)
            transform = move*rotate*scale
            with sc.Transform(transform):
                self._show_uv()
    
    """Main Function to draw UV directly in Omniverse"""
    """Depreciate due to performance issue"""
    def _draw_uv_line(self, point_count, points):
        # point_count = 3
        # points = [[0,0,0],[0,0.5,0],[0.5,0.5,0]]
        vertex_indices = []
        colors = []
        for i in range(point_count):
            vertex_indices.append(i)
            colors.append([0.5, 0.5, 0.5, 1])

        # This will create a new list to append the first element to the list and form a closed line
        line_points = points + [points[0]]
        # Draw UV
        sc.PolygonMesh(points, colors, [point_count], vertex_indices)
        sc.Curve(
            line_points,
            thicknesses=[0.2],
            colors=[0.0, 0.0, 0.0, 1],
            curve_type=sc.Curve.CurveType.LINEAR,
        )

    # Draw a rect in 1:1 to show the UV block
    def _build_safe_rect(self):
        """Build the scene ui graphics for the safe area rectangle

        Args:
            percentage (float): The 0-1 percentage the render target that the rectangle should fill.
            color: The color to draw the rectangle wireframe with.
        """
        transparent_black = (0, 0, 0, 0.1)        
        sc.Rectangle(1, 1, thickness=1, wireframe=False, color=transparent_black)
    
    def _build_axis(self):
            # grid represent 0-1
            sc.Line([0,0,1], [0, 1, 1], thicknesses=[5.0], color=cl.red)
            sc.Line([0,0,1], [1, 0, 1], thicknesses=[5.0], color=cl.red)

    def get_aspect_ratio(self):
        """Get the aspect ratio of the viewport.

        Returns:
            float: The viewport aspect ratio.
        """
        return self._aspect_ratio
    
    def get_width(self):
        """Get the width of the viewport.

        Returns:
            float: The viewport aspect ratio.
        """
        return self._width
    
    def get_height(self):
        """Get the height of the viewport.

        Returns:
            float: The viewport aspect ratio.
        """
        return self._height
    
    def on_model_updated(self, item):
        # Regenerate the manipulator
        self.invalidate()


    """Test Function"""
    def __example_draw_shape(self):
        point_count = 6
        points = [[0,0,0],[0,0.5,0],[0.5,0.5,0],[0.8,0,0],[0.8,0.5,0],[0.8,0.7,0]]
        vertex_indices = []
        sizes = []
        colors = []
        for i in range(point_count):
            weight = i / point_count
            vertex_indices.append(i)
            colors.append([weight, 1 - weight, 1, 1])
            print(vertex_indices)

        sc.PolygonMesh(points, colors, [point_count], vertex_indices)
        #pass