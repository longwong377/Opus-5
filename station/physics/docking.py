"""Docking against a rotating station.

The inverse of the cobra bay launch, and considerably harder. A bay on the
rotating hull is not a fixed target: it is a point travelling at 52.2 m/s on a
circle, whose surface normal sweeps through a full turn every 33.5 seconds. To
dock, a craft has to arrive with matching position *and* matching velocity
*and* matching attitude, all of which are functions of time.

Two approaches exist and the model supports both, because the station uses both:

  * **Spin-match** -- the craft matches the drum's rotation and closes radially.
    This is what a fighter returning to a cobra bay does.
  * **Axial approach** -- the craft holds station on the axis, where there is no
    tangential motion to match at all, and mates with a non-rotating port. This
    is why the forward docking sphere exists and why large ships use it.

Pure Python, no engine. See station/physics/test_docking.py.
"""
import math

from starfury import add, cross, dot, norm, scale, sub, unit


class DockingBay:
    """A bay fixed to the rotating hull.

    Its state is entirely a function of time, so the guidance problem is
    interception of a known trajectory rather than pursuit of a free target.
    """

    def __init__(self, drum, radius, z, phase=0.0):
        self.drum = drum
        self.radius = radius
        self.z = z
        self.phase = phase

    def angle_at(self, t):
        return self.phase + self.drum.omega * t

    def position_at(self, t):
        a = self.angle_at(t)
        return (self.radius * math.cos(a), self.radius * math.sin(a), self.z)

    def velocity_at(self, t):
        a = self.angle_at(t)
        v = self.drum.omega * self.radius
        return (-v * math.sin(a), v * math.cos(a), 0.0)

    def normal_at(self, t):
        """Outward surface normal -- the direction a craft approaches from."""
        a = self.angle_at(t)
        return (math.cos(a), math.sin(a), 0.0)

    def approach_point(self, t, standoff):
        """A point directly outboard of the bay at the given standoff."""
        n = self.normal_at(t)
        p = self.position_at(t)
        return add(p, scale(n, standoff))

    def approach_state(self, t, standoff):
        """Position and velocity of the approach point.

        The approach point orbits too, so its velocity is omega x r at the
        *standoff* radius, not at the bay radius -- a distinction that matters,
        because a craft that matches the bay's velocity while sitting further
        out is not actually station-keeping and will drift aft of the bay.
        """
        n = self.normal_at(t)
        p = add(self.position_at(t), scale(n, standoff))
        v = self.drum.omega * (self.radius + standoff)
        a = self.angle_at(t)
        return p, (-v * math.sin(a), v * math.cos(a), 0.0)


def closing_rate(craft_pos, craft_vel, bay_pos, bay_vel):
    """Rate of approach along the line of sight. Negative means closing.

    The number a pilot actually watches: range rate matters, absolute speed
    does not. Two craft at 50 m/s with zero closing rate are perfectly safe.
    """
    los = sub(bay_pos, craft_pos)
    d = norm(los)
    if d == 0:
        return 0.0
    return -dot(sub(bay_vel, craft_vel), unit(los))


def relative_speed(craft_vel, bay_vel):
    return norm(sub(craft_vel, bay_vel))


def contact_is_safe(craft_pos, craft_vel, bay, t,
                    max_closing=2.0, max_lateral=0.5, max_misalign_deg=8.0):
    """Whether contact at this instant would be a dock rather than a collision.

    Three independent conditions, all of which a real docking system checks:
    closing rate within the buffer's capacity, lateral drift small enough that
    the craft does not scrape along the hull, and attitude aligned with the
    bay's normal.
    """
    bp, bv = bay.position_at(t), bay.velocity_at(t)
    rel = sub(craft_vel, bv)
    n = bay.normal_at(t)
    closing = -dot(rel, n)
    lateral = norm(sub(rel, scale(n, dot(rel, n))))
    los = unit(sub(craft_pos, bp))
    misalign = math.degrees(math.acos(max(-1.0, min(1.0, dot(los, n)))))
    return {
        "safe": closing <= max_closing and lateral <= max_lateral
                and misalign <= max_misalign_deg,
        "closing_rate": closing,
        "lateral_drift": lateral,
        "misalignment_deg": misalign,
    }


def spin_match_velocity(bay, t, standoff):
    """Velocity a craft must hold to stay parked off the bay.

    This is the whole difficulty of docking a rotating station in one number:
    station-keeping is not zero velocity, it is a continuously turning
    velocity of 50+ m/s. A craft that stops dead relative to the station's
    centre will watch the bay swing away from it.
    """
    _p, v = bay.approach_state(t, standoff)
    return v


def axial_approach_is_trivial(drum, z):
    """On the axis there is no tangential motion to match.

    Returns the tangential speed at radius zero, which is identically zero --
    stated as a function because it is the design rationale for the forward
    docking sphere, not merely an arithmetic fact.
    """
    return drum.omega * 0.0
