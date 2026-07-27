"""The core shuttle: axial transit through the gravity gradient.

The shuttle runs along the station's axis, where spin gravity is zero, while
the decks it serves sit out at the rim under a full g. Getting from one to the
other is not a lift ride with a number changing on a display -- it is a
continuous transition from 1 g to weightlessness, and back, with Coriolis
pushing sideways the entire way.

Three things fall out of the geometry and all three are felt:

  * **Gravity ramps linearly with radius.** Halfway to the axis is half a g.
  * **Coriolis deflects radial motion.** Moving inward at speed v produces
    2*omega*v of spinward acceleration -- the car has to be constrained
    against it, and an unconstrained passenger is pushed against one wall.
  * **Tangential speed must be shed.** A car at the rim is moving at 52.2 m/s
    tangentially; on the axis it is moving at zero. That momentum has to go
    somewhere, and it is the reason the transfer is a spiral rather than a
    straight radial drop.

Pure Python, no engine. See station/physics/test_core_shuttle.py.
"""
import math

G0 = 9.80665


class RadialTransit:
    """A car travelling between the rim and the axis.

    Modelled as a constrained body: the track holds it on its radial path, so
    the interesting outputs are the accelerations the passengers feel and the
    force the track has to supply, not a free trajectory.
    """

    def __init__(self, drum, r_start, r_end, duration):
        self.drum = drum
        self.r0 = r_start
        self.r1 = r_end
        self.duration = duration

    def radius_at(self, t):
        """Smoothstep in radius: no jerk at either end, which is what a
        passenger-carrying car would actually do."""
        f = max(0.0, min(1.0, t / self.duration))
        f = f * f * (3.0 - 2.0 * f)
        return self.r0 + (self.r1 - self.r0) * f

    def radial_speed(self, t, h=1e-4):
        return (self.radius_at(t + h) - self.radius_at(t - h)) / (2 * h)

    def gravity_at(self, t):
        """Apparent gravity felt in the car, in m/s^2."""
        return self.drum.omega ** 2 * self.radius_at(t)

    def gravity_in_g(self, t):
        return self.gravity_at(t) / G0

    def coriolis_at(self, t):
        """Lateral acceleration from radial motion. 2*omega*v_radial.

        Signed: negative radial speed (inbound) gives spinward deflection.
        """
        return 2.0 * self.drum.omega * self.radial_speed(t)

    def tangential_speed_at(self, t):
        """Speed the car must be doing tangentially to co-rotate at its
        current radius. Falls to zero on the axis."""
        return self.drum.omega * self.radius_at(t)

    def tangential_accel_at(self, t, h=1e-4):
        """Rate at which tangential speed must be shed. The track supplies
        this, and passengers feel it as a push along the direction of travel
        around the drum."""
        return (self.tangential_speed_at(t + h)
                - self.tangential_speed_at(t - h)) / (2 * h)

    def peak_lateral_g(self):
        n = 400
        return max(abs(self.coriolis_at(self.duration * i / n))
                   for i in range(1, n)) / G0

    def profile(self, samples=40):
        out = []
        for i in range(samples + 1):
            t = self.duration * i / samples
            out.append({
                "t": t,
                "radius_m": self.radius_at(t),
                "gravity_g": self.gravity_in_g(t),
                "coriolis_g": self.coriolis_at(t) / G0,
                "tangential_m_s": self.tangential_speed_at(t),
            })
        return out


def comfortable_duration(drum, r_start, r_end, max_lateral_g=0.12):
    """Shortest transit that keeps Coriolis within a comfort limit.

    This is a real design constraint, not decoration: rush the trip and
    passengers get thrown against the wall by an acceleration with no visible
    cause. Solved by bisection on the peak lateral load.
    """
    lo, hi = 1.0, 3600.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if RadialTransit(drum, r_start, r_end, mid).peak_lateral_g() > max_lateral_g:
            lo = mid
        else:
            hi = mid
    return hi


class AxialShuttle:
    """Transit along the axis itself, where there is no gravity at all."""

    def __init__(self, drum, z0, z1, cruise_accel=1.2):
        self.drum = drum
        self.z0 = z0
        self.z1 = z1
        self.accel = cruise_accel

    @property
    def distance(self):
        return abs(self.z1 - self.z0)

    def transit_time(self):
        """Accelerate to the midpoint, decelerate to the end."""
        return 2.0 * math.sqrt(self.distance / self.accel)

    def peak_speed(self):
        return self.accel * (self.transit_time() / 2.0)
