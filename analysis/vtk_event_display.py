#!/usr/bin/env python3
"""Native VTK event display for the muon active-target Geant4 output."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path


try:
    from vtkmodules.vtkCommonColor import vtkNamedColors
    from vtkmodules.vtkCommonCore import vtkPoints
    from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData
    from vtkmodules.vtkFiltersSources import vtkCubeSource, vtkSphereSource
    from vtkmodules.vtkIOImage import vtkPNGWriter
    from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
    from vtkmodules.vtkRenderingCore import (
        vtkActor,
        vtkCamera,
        vtkPolyDataMapper,
        vtkRenderWindow,
        vtkRenderWindowInteractor,
        vtkRenderer,
        vtkWindowToImageFilter,
    )
    import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
except ImportError as exc:
    raise SystemExit(
        "VTK Python bindings are not available in this Python. Try:\n"
        "  /opt/homebrew/bin/python3.14 analysis/vtk_event_display.py g4_05.wrl\n"
        f"\nOriginal import error: {exc}"
    )


PROJECT_DIR = Path(__file__).resolve().parents[1]
CONVERTER = PROJECT_DIR / "event-display-3d" / "scripts" / "vrml_to_event_json.py"


def load_event(path: Path) -> dict:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text())

    if path.suffix.lower() == ".wrl":
        spec = importlib.util.spec_from_file_location("vrml_to_event_json", CONVERTER)
        if spec is None or spec.loader is None:
            raise SystemExit(f"Could not import converter: {CONVERTER}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.parse_vrml(path)

    raise SystemExit(f"Unsupported input type: {path}")


def path_length(points: list[list[float]]) -> float:
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def point_at(points: list[list[float]], distance: float) -> list[float]:
    if distance <= 0:
        return points[0]

    remaining = distance
    for first, second in zip(points, points[1:]):
        segment = math.dist(first, second)
        if remaining <= segment:
            t = remaining / segment if segment > 0 else 0.0
            return [
                first[axis] + t * (second[axis] - first[axis]) for axis in range(3)
            ]
        remaining -= segment

    return points[-1]


def partial_points(points: list[list[float]], fraction: float) -> list[list[float]]:
    total = path_length(points)
    target = total * max(0.0, min(1.0, fraction))
    if target <= 0:
        return [points[0], points[0]]

    output = [points[0]]
    remaining = target
    for first, second in zip(points, points[1:]):
        segment = math.dist(first, second)
        if remaining >= segment:
            output.append(second)
            remaining -= segment
        else:
            output.append(point_at([first, second], remaining))
            break

    return output


def make_line_polydata(points: list[list[float]]) -> vtkPolyData:
    vtk_points = vtkPoints()
    for point in points:
        vtk_points.InsertNextPoint(point)

    lines = vtkCellArray()
    lines.InsertNextCell(len(points))
    for idx in range(len(points)):
        lines.InsertCellPoint(idx)

    polydata = vtkPolyData()
    polydata.SetPoints(vtk_points)
    polydata.SetLines(lines)
    return polydata


def set_line_points(polydata: vtkPolyData, points: list[list[float]]) -> None:
    next_polydata = make_line_polydata(points)
    polydata.SetPoints(next_polydata.GetPoints())
    polydata.SetLines(next_polydata.GetLines())
    polydata.Modified()


def add_box(renderer: vtkRenderer, box: dict, index: int) -> None:
    source = vtkCubeSource()
    source.SetCenter(*box["center"])
    source.SetXLength(box["size"][0])
    source.SetYLength(box["size"][1])
    source.SetZLength(box["size"][2])

    mapper = vtkPolyDataMapper()
    mapper.SetInputConnection(source.GetOutputPort())

    actor = vtkActor()
    actor.SetMapper(mapper)
    color = (0.30, 0.62, 1.00) if index % 20 < 10 else (1.00, 0.58, 0.16)
    actor.GetProperty().SetColor(*color)
    actor.GetProperty().SetOpacity(0.18)
    actor.GetProperty().SetRepresentationToWireframe()
    actor.GetProperty().SetLineWidth(1.0)
    renderer.AddActor(actor)


def add_reference_line(renderer: vtkRenderer, points: list[list[float]], color, width=1.0):
    polydata = make_line_polydata(points)
    mapper = vtkPolyDataMapper()
    mapper.SetInputData(polydata)
    actor = vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*color)
    actor.GetProperty().SetLineWidth(width)
    renderer.AddActor(actor)
    return actor


class AnimatedTrack:
    def __init__(self, renderer: vtkRenderer, track: dict):
        self.points = track["points"]
        self.length = max(path_length(self.points), 1e-9)
        self.primary = track.get("role") == "primary"
        self.color = (0.91, 0.16, 0.25) if self.primary else (0.18, 0.78, 0.48)

        self.polydata = make_line_polydata([self.points[0], self.points[0]])
        mapper = vtkPolyDataMapper()
        mapper.SetInputData(self.polydata)

        self.actor = vtkActor()
        self.actor.SetMapper(mapper)
        self.actor.GetProperty().SetColor(*self.color)
        self.actor.GetProperty().SetLineWidth(3.0 if self.primary else 1.4)
        renderer.AddActor(self.actor)

        sphere = vtkSphereSource()
        sphere.SetRadius(3.0 if self.primary else 1.7)
        sphere.SetThetaResolution(18)
        sphere.SetPhiResolution(12)
        sphere_mapper = vtkPolyDataMapper()
        sphere_mapper.SetInputConnection(sphere.GetOutputPort())

        self.head = vtkActor()
        self.head.SetMapper(sphere_mapper)
        self.head.GetProperty().SetColor(*self.color)
        renderer.AddActor(self.head)
        self.update(0.0)

    def update(self, progress: float) -> None:
        points = partial_points(self.points, progress)
        set_line_points(self.polydata, points)
        self.head.SetPosition(*point_at(self.points, self.length * progress))
        self.head.SetVisibility(progress > 0.002)


class AnimationTimer:
    def __init__(self, render_window: vtkRenderWindow, tracks, speed: float):
        self.render_window = render_window
        self.tracks = tracks
        self.speed = speed
        self.progress = 0.0
        self.running = True

    def timer(self, _obj, _event):
        if self.running:
            self.progress = (self.progress + self.speed) % 1.0
            for track in self.tracks:
                track.update(self.progress)
            self.render_window.Render()

    def keypress(self, obj, _event):
        key = obj.GetKeySym()
        if key == "space":
            self.running = not self.running
        elif key == "r":
            self.progress = 0.0
            for track in self.tracks:
                track.update(self.progress)
            self.render_window.Render()
        elif key in ("plus", "equal"):
            self.speed *= 1.5
        elif key in ("minus", "underscore"):
            self.speed /= 1.5


def build_scene(event: dict, size: tuple[int, int], offscreen: bool):
    renderer = vtkRenderer()
    renderer.SetBackground(0.03, 0.035, 0.035)

    render_window = vtkRenderWindow()
    render_window.SetWindowName("Muon Active Target Geant4 Event Display")
    render_window.SetSize(*size)
    render_window.AddRenderer(renderer)
    render_window.SetOffScreenRendering(1 if offscreen else 0)

    for index, box in enumerate(event["detector"]):
        add_box(renderer, box, index)

    add_reference_line(renderer, [[0, 0, -180], [0, 0, 160]], (0.62, 0.78, 1.0), 2.0)
    add_reference_line(renderer, [[-70, 0, 0], [70, 0, 0]], (0.8, 0.8, 0.8), 1.0)
    add_reference_line(renderer, [[0, -70, 0], [0, 70, 0]], (0.8, 0.8, 0.8), 1.0)

    tracks = [AnimatedTrack(renderer, track) for track in event["tracks"]]

    camera = vtkCamera()
    camera.SetPosition(155, 125, 335)
    camera.SetFocalPoint(0, 0, -20)
    camera.SetViewUp(0, 1, 0)
    renderer.SetActiveCamera(camera)
    renderer.ResetCameraClippingRange()

    return renderer, render_window, tracks


def write_screenshot(render_window: vtkRenderWindow, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    capture = vtkWindowToImageFilter()
    capture.SetInput(render_window)
    capture.Update()

    writer = vtkPNGWriter()
    writer.SetFileName(str(path))
    writer.SetInputConnection(capture.GetOutputPort())
    writer.Write()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input",
        nargs="?",
        default=str(PROJECT_DIR / "event-display-3d" / "public" / "event.json"),
        help="Input .json from event-display-3d or Geant4 .wrl file.",
    )
    parser.add_argument("--screenshot", help="Write a PNG screenshot and exit.")
    parser.add_argument("--size", default="1280x900", help="Window size, e.g. 1280x900.")
    parser.add_argument("--speed", type=float, default=0.006, help="Animation step per timer tick.")
    args = parser.parse_args()

    width, height = [int(part) for part in args.size.lower().split("x", 1)]
    event = load_event(Path(args.input))
    offscreen = args.screenshot is not None
    _renderer, render_window, tracks = build_scene(event, (width, height), offscreen)

    if args.screenshot:
        for track in tracks:
            track.update(1.0)
        render_window.Render()
        write_screenshot(render_window, Path(args.screenshot))
        print(f"wrote {args.screenshot}")
        print(f"detector boxes: {len(event['detector'])}")
        print(f"tracks: {len(event['tracks'])}")
        return

    interactor = vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)
    interactor.SetInteractorStyle(vtkInteractorStyleTrackballCamera())

    timer = AnimationTimer(render_window, tracks, args.speed)
    interactor.AddObserver("TimerEvent", timer.timer)
    interactor.AddObserver("KeyPressEvent", timer.keypress)

    print("Controls: mouse rotate/zoom/pan, space pause/resume, r reset, +/- speed.")
    render_window.Render()
    interactor.Initialize()
    interactor.CreateRepeatingTimer(30)
    interactor.Start()


if __name__ == "__main__":
    main()
