"""Newtonian flight model for the Aurora-class Starfury.

The Starfury's whole design premise is that it is not an aeroplane. It has no
lift surfaces and no preferred direction of travel: four thruster booms at the
corners plus RCS let it rotate freely while its velocity continues unchanged.
Flying backwards while decelerating is normal operation, not a trick.

Two consequences drive the model:

  * Attitude and velocity are fully independent. There is no coupling that
    turns the nose into the direction of motion, because nothing in vacuum
    provides one.
  * Thrust must be *allocated* across discrete thrusters rather than applied as
    an abstract force vector. A commanded translation the thrusters cannot
    produce should come out partially satisfied, not silently exact.

Pure Python, no engine. See station/physics/test_starfury.py.
"""
import math
from dataclasses import dataclass, field


def _v(a, b, f):
    return (f(a[0], b[0]), f(a[1], b[1]), f(a[2], b[2]))


def add(a, b):
    return _v(a, b, lambda x, y: x + y)


def sub(a, b):
    return _v(a, b, lambda x, y: x - y)


def scale(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def norm(a):
    return math.sqrt(dot(a, a))


def unit(a):
    n = norm(a)
    return (0.0, 0.0, 0.0) if n == 0 else scale(a, 1.0 / n)


@dataclass(frozen=True)
class Thruster:
    """One thruster: where it sits on the hull and which way it pushes.

    `direction` is the direction of the force it applies to the craft, in body
    frame -- the opposite of where its plume goes.
    """
    name: str
    position: tuple      # m, body frame, relative to centre of mass
    direction: tuple     # unit vector, body frame
    max_thrust: float    # N

    def force(self, throttle):
        return scale(self.direction, self.max_thrust * max(0.0, min(1.0, throttle)))

    def torque(self, throttle):
        return cross(self.position, self.force(throttle))


def aurora_thrusters(main_thrust=68_000.0, rcs_thrust=4_200.0):
    """The SA-23E Aurora's layout: four corner booms plus RCS quads.

    The four mains sit outboard on the booms rather than on the centreline,
    which is why the Starfury can pitch and yaw hard using main thrust alone --
    each boom has real leverage about the centre of mass.
    """
    t = []
    boom = 3.4          # m outboard on each diagonal
    aft = -2.1          # m aft of the centre of mass
    for sx in (1, -1):
        for sy in (1, -1):
            t.append(Thruster(f"main_{'u' if sy > 0 else 'l'}{'r' if sx > 0 else 'l'}",
                              (sx * boom, sy * boom, aft), (0.0, 0.0, 1.0), main_thrust))
    # RCS quads: lateral, vertical and retro authority.
    for sx in (1, -1):
        t.append(Thruster(f"rcs_lat_{'r' if sx > 0 else 'l'}",
                          (sx * boom, 0.0, 0.0), (-sx, 0.0, 0.0), rcs_thrust))
    for sy in (1, -1):
        t.append(Thruster(f"rcs_vert_{'u' if sy > 0 else 'd'}",
                          (0.0, sy * boom, 0.0), (0.0, -sy, 0.0), rcs_thrust))
    t.append(Thruster("rcs_retro", (0.0, 0.0, 2.4), (0.0, 0.0, -1.0), rcs_thrust * 2))
    return t


@dataclass
class Starfury:
    """Rigid-body state and integration.

    Attitude is carried as a quaternion (w, x, y, z) so that repeated rotation
    never gimbal-locks -- which matters here more than in most craft, because
    the Starfury genuinely does spend time pointing every direction.
    """
    mass: float = 14_800.0                 # kg, loaded
    inertia: tuple = (52_000.0, 52_000.0, 31_000.0)   # kg m^2, body axes
    position: tuple = (0.0, 0.0, 0.0)      # m, world
    velocity: tuple = (0.0, 0.0, 0.0)      # m/s, world
    orientation: tuple = (1.0, 0.0, 0.0, 0.0)
    angular_velocity: tuple = (0.0, 0.0, 0.0)   # rad/s, body frame
    thrusters: list = field(default_factory=aurora_thrusters)

    # --- attitude helpers ---------------------------------------------------

    def body_to_world(self, v):
        w, x, y, z = self.orientation
        t = scale(cross((x, y, z), v), 2.0)
        return add(add(v, scale(t, w)), cross((x, y, z), t))

    def world_to_body(self, v):
        w, x, y, z = self.orientation
        inv = (w, -x, -y, -z)
        saved, self.orientation = self.orientation, inv
        try:
            return self.body_to_world(v)
        finally:
            self.orientation = saved

    @property
    def forward(self):
        return self.body_to_world((0.0, 0.0, 1.0))

    def normalise(self):
        w, x, y, z = self.orientation
        n = math.sqrt(w * w + x * x + y * y + z * z)
        if n > 0:
            self.orientation = (w / n, x / n, y / n, z / n)

    # --- allocation ---------------------------------------------------------

    def allocate(self, translate, rotate):
        """Throttle each thruster to best approximate the commanded demand.

        Deliberately simple and honest: each thruster opens in proportion to
        how well it serves the demand, and a demand the layout cannot satisfy
        comes out partially satisfied rather than silently exact. Pretending
        otherwise would make the craft feel like it has thrusters it does not.
        """
        out = {}
        tw = unit(translate) if norm(translate) > 0 else (0.0, 0.0, 0.0)
        rw = unit(rotate) if norm(rotate) > 0 else (0.0, 0.0, 0.0)
        for th in self.thrusters:
            lin = dot(th.direction, tw) * norm(translate)
            tq = th.torque(1.0)
            rot = dot(unit(tq), rw) * norm(rotate) if norm(tq) > 0 else 0.0
            out[th.name] = max(0.0, min(1.0, lin + rot))
        return out

    def net(self, throttles):
        f = (0.0, 0.0, 0.0)
        t = (0.0, 0.0, 0.0)
        for th in self.thrusters:
            k = throttles.get(th.name, 0.0)
            if k <= 0:
                continue
            f = add(f, th.force(k))
            t = add(t, th.torque(k))
        return f, t

    # --- integration --------------------------------------------------------

    def step(self, dt, throttles=None, external_accel=(0.0, 0.0, 0.0)):
        """Advance by dt. Semi-implicit Euler: stable and momentum-preserving
        at the step sizes a flight model runs at."""
        force_body, torque_body = self.net(throttles or {})

        accel = add(scale(self.body_to_world(force_body), 1.0 / self.mass),
                    external_accel)
        self.velocity = add(self.velocity, scale(accel, dt))
        self.position = add(self.position, scale(self.velocity, dt))

        ix, iy, iz = self.inertia
        wx, wy, wz = self.angular_velocity
        # Euler's equations: the gyroscopic term is what makes a tumbling
        # Starfury precess instead of spinning about a fixed body axis.
        gyro = ((iy - iz) * wy * wz, (iz - ix) * wz * wx, (ix - iy) * wx * wy)
        alpha = ((torque_body[0] + gyro[0]) / ix,
                 (torque_body[1] + gyro[1]) / iy,
                 (torque_body[2] + gyro[2]) / iz)
        self.angular_velocity = add(self.angular_velocity, scale(alpha, dt))

        wx, wy, wz = self.angular_velocity
        w, x, y, z = self.orientation
        self.orientation = (
            w + 0.5 * dt * (-x * wx - y * wy - z * wz),
            x + 0.5 * dt * (w * wx + y * wz - z * wy),
            y + 0.5 * dt * (w * wy + z * wx - x * wz),
            z + 0.5 * dt * (w * wz + x * wy - y * wx),
        )
        self.normalise()

    # --- derived ------------------------------------------------------------

    @property
    def speed(self):
        return norm(self.velocity)

    def max_linear_accel(self):
        """Along the mains, at full throttle."""
        return sum(t.max_thrust for t in self.thrusters
                   if t.name.startswith("main_")) / self.mass

    def launch_from_drum(self, drum, radius, z, throttles=None):
        """Place the craft in a cobra bay and release it.

        The bay is on the rotating hull, so the craft leaves already carrying
        the drum's tangential velocity. That inheritance is the launch: the
        station throws the Starfury clear, which is exactly what the show
        depicts and what makes cobra bays work without a catapult.
        """
        self.position = (radius, 0.0, z)
        self.velocity = (0.0, drum.omega * radius, 0.0)
        return self.velocity
