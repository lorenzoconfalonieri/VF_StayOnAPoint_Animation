"""
Visualization of the polyhedral approximation used in §22.3.1 (VF1 — "Stay on a Point")
of Li, Kapoor & Taylor, "Telerobot Control by Virtual Fixtures for Surgical Applications."

The ideal constraint    ‖δ_p + Δx_p‖ ≤ ε₁      (eq. 22.7)
keeps the task-frame position inside a sphere of radius ε₁ around the target x_p^d.
To stay in an LP/QP, the sphere is replaced by the intersection of n·m half-spaces
    n̂_{ij} · (δ_p + Δx_p) ≤ ε₁                (eq. 22.8)
whose outward normals sample the unit sphere via two angle grids:
    α_i = (i+½)·π/n − π/2,   i = 0 … n-1   (elevation: south pole → north pole)
    β_j = j·2π/m,             j = 0 … m-1   (azimuth)
    n̂_{ij} = (cos α_i cos β_j,  cos α_i sin β_j,  sin α_i)

Render with:
    manim -pql vf1_polyhedron.py VF1Polyhedron
    manim -pql vf1_polyhedron.py VF1Convergence
    manim -pql vf1_polyhedron.py VF1HalfSpace
    manim -pql vf1_polyhedron.py VF1VaryNM
"""

import numpy as np
from manim import (
    ThreeDScene, ThreeDAxes, Sphere, Dot3D, Arrow3D, Polyhedron, Text, MathTex,
    VGroup, Create, FadeIn, FadeOut, Transform, FadeTransform,
    WHITE, BLUE, YELLOW, RED, GREEN, TEAL, ORANGE, DEGREES,
    UP, DOWN, LEFT, RIGHT, UL, UR, DR,
)

EPS = 2.0  # ε₁, sphere radius (scaled for visibility)

# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def face_normals(n: int, m: int) -> np.ndarray:
    """The n·m outward face normals n̂_{ij} from eq. (22.8)."""
    alpha = (np.arange(n) + 0.5) * np.pi / n - np.pi / 2
    beta  = np.arange(m) * 2 * np.pi / m
    A, B  = np.meshgrid(alpha, beta, indexing="ij")
    return np.stack([np.cos(A) * np.cos(B),
                     np.cos(A) * np.sin(B),
                     np.sin(A)], axis=-1).reshape(-1, 3)


def polyhedron_vertices_faces(n: int, m: int, radius: float = EPS):
    """
    Intersect n·m half-spaces  n̂·x ≤ radius  with scipy, then convex-hull
    the intersection vertices.  Returns (vertex_list, face_index_list).
    """
    from scipy.spatial import HalfspaceIntersection, ConvexHull

    normals = face_normals(n, m)
    # drop near-duplicates that arise at poles
    keep = []
    for v in normals:
        if not any(np.allclose(v, k, atol=1e-6) for k in keep):
            keep.append(v)
    normals = np.array(keep)

    hs = np.hstack([normals, -radius * np.ones((len(normals), 1))])
    pts = HalfspaceIntersection(hs, np.zeros(3)).intersections
    hull = ConvexHull(pts)
    remap = {old: new for new, old in enumerate(hull.vertices)}
    verts = hull.points[hull.vertices].tolist()
    faces = [[remap[i] for i in s] for s in hull.simplices]
    return verts, faces


_poly_cache: dict = {}

def make_polyhedron(n: int, m: int, radius: float = EPS) -> Polyhedron:
    """Build (and cache) a Manim Polyhedron for the given (n, m)."""
    key = (n, m, radius)
    if key not in _poly_cache:
        verts, faces = polyhedron_vertices_faces(n, m, radius)
        _poly_cache[key] = (verts, faces)
    verts, faces = _poly_cache[key]
    return Polyhedron(
        vertex_coords=verts,
        faces_list=faces,
        faces_config={"fill_opacity": 0.25, "stroke_width": 1.5,
                      "stroke_color": YELLOW, "fill_color": YELLOW},
        graph_config={"vertex_config": {"radius": 0.02, "color": WHITE},
                      "edge_config": {"stroke_color": WHITE, "stroke_width": 1.0}},
    )


def _label(text: str) -> MathTex:
    return MathTex(text).scale(0.75).to_corner(UR)


def _sphere(opacity=0.10):
    return Sphere(radius=EPS, resolution=(12, 24)).set_opacity(opacity).set_color(BLUE)


def _axes():
    return ThreeDAxes(x_range=[-3,3,1], y_range=[-3,3,1], z_range=[-3,3,1],
                      x_length=6, y_length=6, z_length=6)


# ---------------------------------------------------------------------------
# Scene 1 — anatomy: target point, error vector, sphere, polyhedron
# ---------------------------------------------------------------------------

class VF1Polyhedron(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=65*DEGREES, theta=35*DEGREES, zoom=0.9)
        self.add(_axes())

        target  = Dot3D(np.zeros(3), color=RED,    radius=0.08)
        dp      = np.array([0.9, 0.4, 0.3])
        ddx     = np.array([0.25, -0.15, 0.4])
        current = Dot3D(dp,       color=ORANGE, radius=0.06)
        nxt     = Dot3D(dp + ddx, color=GREEN,  radius=0.06)
        v_delta = Arrow3D(np.zeros(3), dp,       color=ORANGE, thickness=0.015)
        v_dx    = Arrow3D(dp,          dp + ddx, color=GREEN,  thickness=0.015)

        sphere = _sphere(0.12)
        poly   = make_polyhedron(12, 12)

        # 3D floating labels — add_fixed_orientation_mobjects keeps them
        # facing the camera while staying anchored at a 3D position.
        off = np.array([0.18, 0.18, 0.18])
        lbl_target  = MathTex(r"x_p^d",               color=RED   ).scale(0.6)
        lbl_current = MathTex(r"\delta_p",             color=ORANGE).scale(0.6)
        lbl_nxt     = MathTex(r"\delta_p+\Delta x_p", color=GREEN ).scale(0.6)
        lbl_eps     = MathTex(r"\varepsilon_1",        color=BLUE  ).scale(0.55)

        lbl_target .move_to(np.zeros(3) + off)
        lbl_current.move_to(dp          + off)
        lbl_nxt    .move_to(dp + ddx    + off)
        lbl_eps    .move_to(np.array([EPS * 0.62, EPS * 0.62, EPS * 0.35]))

        # Start all labels invisible so FadeIn controls exactly when each appears.
        for lbl in [lbl_target, lbl_current, lbl_nxt, lbl_eps]:
            lbl.set_opacity(0)
        self.add_fixed_orientation_mobjects(lbl_target, lbl_current, lbl_nxt, lbl_eps)

        title = Text("VF1 — Stay on a Point", font_size=32).to_corner(UL)
        eq = MathTex(r"\|", r"\delta_p", r"+", r"\Delta x_p",
                     r"\| \le \varepsilon_1", r"\;(n{=}12,\,m{=}12)"
                     ).scale(0.7).to_corner(UR)
        eq[1].set_color(ORANGE)
        eq[3].set_color(GREEN)
        self.add_fixed_in_frame_mobjects(title, eq)

        # 1 — target point + sphere
        self.play(FadeIn(target), FadeIn(sphere))
        self.play(FadeIn(lbl_target), FadeIn(lbl_eps))

        # 2 — vectors appear; labels come in after a full rotation
        self.play(Create(v_delta), FadeIn(current))
        self.play(Create(v_dx),    FadeIn(nxt))

        # full rotation so the viewer sees the 3D vectors from all angles
        self.begin_ambient_camera_rotation(rate=0.25)
        self.wait(4)   # ~one full revolution at rate=0.25 (2π/0.25 ≈ 25s, so ~57° sweep in 4s looks good)
        self.stop_ambient_camera_rotation()

        # labels fade in now that the viewer knows what the vectors are
        self.play(FadeIn(lbl_current), FadeIn(lbl_nxt))
        self.wait(0.5)

        # 3 — polyhedral approximation
        self.play(FadeIn(poly))
        self.begin_ambient_camera_rotation(rate=0.2)
        self.wait(5)
        self.stop_ambient_camera_rotation()


# ---------------------------------------------------------------------------
# Scene 2 — as n×m grows, polyhedron collapses onto the sphere
# ---------------------------------------------------------------------------

class VF1Convergence(ThreeDScene):
    def construct(self):
        # pre-compute all polyhedra so transitions are instant
        configs = [(3,3), (4,4), (6,6), (8,10), (12,16), (24,24)]
        polys   = {(n,m): make_polyhedron(n, m) for n, m in configs}

        self.set_camera_orientation(phi=70*DEGREES, theta=30*DEGREES, zoom=0.95)
        self.add(_axes(), _sphere())

        lbl   = _label(r"n \times m = 3 \times 3")
        title = Text("Polyhedral approximation of the sphere", font_size=28).to_corner(UL)
        self.add_fixed_in_frame_mobjects(title, lbl)

        def rotate_briefly(duration=1.5):
            self.begin_ambient_camera_rotation(rate=0.25)
            self.wait(duration)
            self.stop_ambient_camera_rotation()

        poly = polys[(3, 3)]
        self.play(FadeIn(poly))
        rotate_briefly()

        for n, m in configs[1:]:
            new_poly = polys[(n, m)]
            new_lbl  = _label(fr"n \times m = {n} \times {m}")
            self.add_fixed_in_frame_mobjects(new_lbl)
            self.play(
                FadeTransform(poly, new_poly),
                FadeOut(lbl),
                FadeIn(new_lbl),
                run_time=0.9,
            )
            self.remove(lbl)
            lbl  = new_lbl
            poly = new_poly
            rotate_briefly(2.5 if (n, m) == configs[-1] else 1.5)

        self.begin_ambient_camera_rotation(rate=0.2)
        self.wait(4)
        self.stop_ambient_camera_rotation()


# ---------------------------------------------------------------------------
# Scene 3 — one half-space n̂_{ij}·x ≤ ε₁ then the full polyhedron
# ---------------------------------------------------------------------------

class VF1HalfSpace(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=65*DEGREES, theta=40*DEGREES, zoom=0.95)
        self.add(_axes(), _sphere(0.15))

        n, m = 6, 8
        i, j = 2, 3
        alpha = (i + 0.5) * np.pi / n - np.pi / 2
        beta  = j * 2 * np.pi / m
        nhat  = np.array([np.cos(alpha)*np.cos(beta),
                          np.cos(alpha)*np.sin(beta),
                          np.sin(alpha)])
        center = EPS * nhat
        tmp = np.array([0,0,1.0]) if abs(nhat[2]) < 0.9 else np.array([1.0,0,0])
        u = np.cross(nhat, tmp); u /= np.linalg.norm(u)
        v = np.cross(nhat, u)
        s = 1.2
        corners = [center + a*u + b*v for a,b in [(-s,-s),(s,-s),(s,s),(-s,s)]]

        face = Polyhedron(
            vertex_coords=[c.tolist() for c in corners],
            faces_list=[[0,1,2,3]],
            faces_config={"fill_opacity": 0.45, "fill_color": TEAL, "stroke_color": TEAL},
        )
        arrow = Arrow3D(center, center + 0.8*nhat, color=YELLOW, thickness=0.02)

        # 3D label anchored near the arrow tip
        arrow_tip = center + 0.8*nhat
        lbl_nhat = MathTex(r"\hat{n}_{ij}", color=YELLOW).scale(0.65)
        lbl_nhat.move_to(arrow_tip + nhat * 0.3 + np.array([0.1, 0.1, 0.1]))
        lbl_nhat.set_opacity(0)
        self.add_fixed_orientation_mobjects(lbl_nhat)

        # Bottom-right block: n, m values (persistent across both parts of the scene)
        nm_lbl = VGroup(
            Text(f"n = {n}", font_size=22),
            Text(f"m = {m}", font_size=22),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).to_corner(DR)
        self.add_fixed_in_frame_mobjects(nm_lbl)

        title_poly = Text(f"Full polyhedron: {n}×{m} = {n*m} half-spaces",
                          font_size=28).to_corner(UL)
        self.add_fixed_in_frame_mobjects(title_poly)

        # 1 — show the full polyhedron first and rotate
        poly = make_polyhedron(n, m)
        self.play(FadeIn(poly), FadeIn(nm_lbl))
        self.begin_ambient_camera_rotation(rate=0.25)
        self.wait(4)
        self.stop_ambient_camera_rotation()

        # 2 — swap title, fade out polyhedron, reveal one half-space + normal
        title_hs = Text("One half-space face", font_size=28).to_corner(UL)
        eq = VGroup(
            MathTex(r"\hat{n}_{ij} \cdot (\delta_p + \Delta x_p) \leq \varepsilon_1"),
            MathTex(r"\hat{n}_{ij} = (\cos\alpha_i\cos\beta_j,\ \cos\alpha_i\sin\beta_j,\ \sin\alpha_i)"),
            MathTex(r"\alpha_i = \tfrac{i \cdot 2\pi}{n}, \quad \beta_j = \tfrac{j \cdot 2\pi}{m}"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).scale(0.52).to_corner(UL).shift(DOWN * 0.7)
        ij_lbl = Text(f"face  i = {i},  j = {j}", font_size=20).to_edge(DOWN)
        self.add_fixed_in_frame_mobjects(title_hs, eq, ij_lbl)

        self.play(
            FadeOut(poly),
            FadeOut(title_poly),
            FadeIn(title_hs),
            run_time=0.7,
        )
        self.play(FadeIn(face), Create(arrow), FadeIn(eq), FadeIn(ij_lbl), FadeIn(lbl_nhat))
        self.begin_ambient_camera_rotation(rate=0.25)
        self.wait(5)
        self.stop_ambient_camera_rotation()


# ---------------------------------------------------------------------------
# Scene 4 — vary n and m independently
#   Part A: fix m=4, sweep n  → latitude rings change
#   Part B: fix n=4, sweep m  → longitude wedges change
#   Part C: n=m together      → joint convergence
# ---------------------------------------------------------------------------

class VF1VaryNM(ThreeDScene):
    def construct(self):
        # Warm _poly_cache for all configs upfront so scipy doesn't run mid-animation.
        for cfg in [(3,4),(4,4),(6,4),(10,4),(24,4),(4,3),(4,6),(4,10),(4,24),(6,6),(8,8),(12,12),(24,24)]:
            verts, faces = polyhedron_vertices_faces(*cfg)
            _poly_cache[cfg + (EPS,)] = (verts, faces)

        self.set_camera_orientation(phi=65*DEGREES, theta=35*DEGREES, zoom=0.95)
        self.add(_axes(), _sphere())

        title = Text("Fix  m = 4,  vary  n  (latitude rings)", font_size=26).to_corner(UL)
        lbl   = _label(r"n=3,\ m=4")
        self.add_fixed_in_frame_mobjects(title, lbl)

        poly = make_polyhedron(3, 4)
        self.play(FadeIn(poly))
        self.wait(0.5)

        def swap_lbl(old, new_tex):
            """Fade out fixed-frame label, fade in new one. Returns the new label."""
            new = _label(new_tex)
            self.add_fixed_in_frame_mobjects(new)
            self.play(FadeOut(old), FadeIn(new), run_time=0.4)
            self.remove(old)
            return new

        def swap_title(old, new_text):
            new = Text(new_text, font_size=26).to_corner(UL)
            self.add_fixed_in_frame_mobjects(new)
            self.play(FadeOut(old), FadeIn(new), run_time=0.4)
            self.remove(old)
            return new

        def rotate_briefly(duration=1.5):
            self.begin_ambient_camera_rotation(rate=0.25)
            self.wait(duration)
            self.stop_ambient_camera_rotation()

        # Part A: vary n, fix m=4
        rotate_briefly()
        for n_val in [4, 6, 10, 24]:
            new_poly = make_polyhedron(n_val, 4)
            self.play(FadeTransform(poly, new_poly), run_time=0.9)
            lbl  = swap_lbl(lbl, fr"n={n_val},\ m=4")
            poly = new_poly
            rotate_briefly()

        # Part B: vary m, fix n=4
        title = swap_title(title, "Fix  n = 4,  vary  m  (longitude wedges)")

        new_poly = make_polyhedron(4, 3)
        self.play(FadeTransform(poly, new_poly), run_time=0.9)
        lbl  = swap_lbl(lbl, r"n=4,\ m=3")
        poly = new_poly
        rotate_briefly()

        for m_val in [4, 6, 10, 24]:
            new_poly = make_polyhedron(4, m_val)
            self.play(FadeTransform(poly, new_poly), run_time=0.9)
            lbl  = swap_lbl(lbl, fr"n=4,\ m={m_val}")
            poly = new_poly
            rotate_briefly()

        # Part C: n=m together
        title = swap_title(title, "Vary  n = m  together  →  sphere")

        for k in [6, 8, 12, 24]:
            new_poly = make_polyhedron(k, k)
            self.play(FadeTransform(poly, new_poly), run_time=0.9)
            lbl  = swap_lbl(lbl, fr"n=m={k}")
            poly = new_poly
            rotate_briefly(2.5 if k >= 12 else 1.5)

        self.begin_ambient_camera_rotation(rate=0.2)
        self.wait(4)
        self.stop_ambient_camera_rotation()
