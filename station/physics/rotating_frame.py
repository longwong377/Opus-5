"""Physics of the rotating habitat drum.

This is the most distinctive simulation problem in the project. Everything
inside the drum lives in a frame rotating at omega about +Z, and the "gravity"
people walk in is not a force at all -- it is the floor accelerating them
inward. Getting this right is what makes standing in the drum feel like
Babylon 5 rather than like a corridor with gravity switched on.

Implemented and unit-tested here in pure Python, with no engine and no GPU, so
the maths is proven before any of it reaches Godot. Constants come from
station/schema/station.yaml, which derives them from canon.

Conventions (see the schema's coordinate block):
  * +Z is the station's long axis, fore-positive.
  * Rotation is about +Z at omega rad/s.
  * Spin gravity points radially OUTWARD. For anyone standing on the inner
    surface of the drum, "down" is +radial and "up" is toward the axis.
"""
import math
from dataclasses import dataclass

G0 = 9.80665


@dataclass(frozen=True)
class DrumFrame:
    """A rotating reference frame: the habitat drum and everything in it."""

    omega: float           # rad/s about +Z
    floor_radius: float    # m, the inner surface people stand on

    # --- scalar relations ---------------------------------------------------

    def gravity_at(self, r: float) -> float:
        """Centripetal acceleration magnitude at radius r. a = omega^2 * r.

        Falls linearly to zero on the axis, which is why the core shuttle is
        weightless and why a lift ride from rim to axis is a gravity ramp
        rather than a transition.
        """
        return self.omega * self.omega * r

    def gravity_in_g(self, r: float) -> float:
        return self.gravity_at(r) / G0

    def radius_for_gravity(self, g_fraction: float) -> float:
        """Radius at which spin gravity equals g_fraction of Earth normal."""
        return g_fraction * G0 / (self.omega * self.omega)

    @property
    def period(self) -> float:
        return 2.0 * math.pi / self.omega

    @property
    def rpm(self) -> float:
        return 60.0 / self.period

    @property
    def floor_speed(self) -> float:
        """Tangential speed of the floor. Also the speed the drum surface is
        doing relative to the non-rotating hull, which the docking bays and the
        core shuttle both have to match."""
        return self.omega * self.floor_radius

    # --- fictitious accelerations -------------------------------------------

    def centrifugal(self, pos):
        """Outward acceleration on a body at pos in the rotating frame.

        a = -omega x (omega x r), which for rotation about +Z reduces to
        omega^2 * (x, y, 0) -- purely radial, no axial component.
        """
        x, y, _z = pos
        w2 = self.omega * self.omega
        return (w2 * x, w2 * y, 0.0)

    def coriolis(self, vel):
        """Coriolis acceleration on a body moving at vel in the rotating frame.

        a = -2 * omega x v. For rotation about +Z this is
        2*omega*(vy, -vx, 0): motion along the axis is unaffected, but anything
        moving within the drum's cross-section gets deflected.

        This is the effect that makes the drum feel like a rotating habitat and
        not a room. Walking along the drum's circumference changes your
        apparent weight; climbing a ladder toward the axis pushes you sideways;
        a dropped object lands ahead of where it was released.
        """
        vx, vy, _vz = vel
        k = 2.0 * self.omega
        return (k * vy, -k * vx, 0.0)

    def total_fictitious(self, pos, vel):
        """Sum of centrifugal and Coriolis -- everything a body in the rotating
        frame feels beyond real forces."""
        cf = self.centrifugal(pos)
        co = self.coriolis(vel)
        return (cf[0] + co[0], cf[1] + co[1], cf[2] + co[2])

    # --- apparent weight ----------------------------------------------------

    def apparent_weight_factor(self, r: float, tangential_speed: float) -> float:
        """Weight multiplier for someone moving tangentially at radius r.

        Walking spinward adds to the local rotation and increases weight;
        walking anti-spinward reduces it. The effect is
        (omega*r + v)^2 / (omega*r)^2 and is genuinely noticeable: at the
        habitat floor a brisk walk changes apparent weight by a few percent,
        which is a real, felt characteristic of living in a spun habitat.
        """
        v_floor = self.omega * r
        if v_floor == 0.0:
            return 0.0
        return ((v_floor + tangential_speed) ** 2) / (v_floor ** 2)

    # --- frame transforms ---------------------------------------------------

    def to_inertial(self, pos, t: float):
        """Rotating-frame position -> station inertial frame at time t."""
        a = self.omega * t
        c, s = math.cos(a), math.sin(a)
        x, y, z = pos
        return (c * x - s * y, s * x + c * y, z)

    def to_rotating(self, pos, t: float):
        """Station inertial frame -> rotating-frame position at time t."""
        a = -self.omega * t
        c, s = math.cos(a), math.sin(a)
        x, y, z = pos
        return (c * x - s * y, s * x + c * y, z)

    def velocity_to_inertial(self, pos, vel, t: float):
        """Rotating-frame velocity -> inertial, adding frame motion omega x r.

        Needed wherever something crosses between frames: a Starfury leaving a
        cobra bay inherits the drum's tangential velocity, which is what makes
        the launch a fling rather than a drop.
        """
        x, y, _z = pos
        vx, vy, vz = vel
        vx_i = vx - self.omega * y
        vy_i = vy + self.omega * x
        return self.to_inertial((vx_i, vy_i, vz), t)


def from_schema(schema) -> DrumFrame:
    rot = schema["station"]["rotation"]
    return DrumFrame(
        omega=rot["omega_rad_s"]["value"],
        floor_radius=rot["habitat_floor_radius_m"]["value"],
    )
