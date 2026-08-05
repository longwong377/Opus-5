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

## THE GUIDANCE LAW (session 4p)

Everything above this line describes the *problem*. `plan_approach`, `command`
and `fly` are the *answer*: a two-stage law that takes a Starfury from anywhere
in the neighbourhood to hard contact in a rotating cobra bay, and refuses when
the arithmetic says it cannot.

The refusal is the interesting half. A craft holding station at radius R off a
hub turning at omega is accelerated inward at omega^2 R for as long as it stays
there -- not a manoeuvre with a delta-v, a CONTINUOUS acceleration. Beyond
`amax / omega^2` there is no guidance law at all, only a craft that cannot
follow the circle. `plan_approach` computes that ceiling from the airframe and
the spin and raises `InfeasibleApproach` rather than flying a trajectory it
cannot hold, and `starfury_scene.py --dock-gate` shows it refusing.

Nothing here is a chosen number. The hold standoff falls out of a stated control
reserve, the closing rate falls out of `contact_is_safe`'s own buffer limit, and
the terminal gains fall out of splitting the reserve between the position and
velocity halves of the error. See INV-398..INV-401.
"""
import math
from dataclasses import dataclass, field

from starfury import Starfury, add, cross, dot, norm, scale, sub, unit


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


def corotation_velocity(drum, pos):
    """The velocity a point RIGIDLY ATTACHED TO THE STATION has at `pos`.

    omega x r, evaluated at the craft's own position rather than at the bay's.
    This is the reference a docking clamp actually feels, and it is not the same
    as the bay's velocity -- see `contact_report`.
    """
    return (-drum.omega * pos[1], drum.omega * pos[0], 0.0)


def contact_report(bay, t, pos, vel, max_closing=2.0, max_lateral=0.5,
                   max_misalign_deg=8.0):
    """`contact_is_safe`, referenced to the right velocity.

    A FINDING, AND IT IS ABOUT THE OLD FUNCTION RATHER THAN THE NEW LAW.
    `contact_is_safe` measures the craft's velocity against `bay.velocity_at(t)`
    -- the velocity of the bay's own reference point. A docking craft's CENTRE
    is not at that point: it stands off by its own half-length, 3.0 m for this
    airframe, and a craft co-rotating perfectly at that offset is moving
    omega * 3.0 = 0.563 m/s faster than the bay. The function's own lateral
    limit is 0.5 m/s. **A perfectly flown dock therefore fails its lateral test
    by construction, and by more than the limit.**

    Measured on the first converged run: lateral drift 0.4994 m/s against a
    0.5000 limit -- it passed by 0.0006 m/s, and it passed by luck, because the
    craft happened to settle 2.59 m out rather than 3.00.

    Referencing to `corotation_velocity` at the craft's own position removes the
    term entirely: what is left is the SLIP against the rotating structure,
    which is what a clamp has to absorb and what the limit was written about.
    `spin_match_velocity`'s docstring already says this in words -- "a craft
    that matches the bay's velocity while sitting further out is not actually
    station-keeping" -- and no gate had applied it.

    Both verdicts are returned. `contact_is_safe` is not changed: fifteen tests
    depend on it and its arithmetic is correct for a craft AT the bay.
    """
    ref = corotation_velocity(bay.drum, pos)
    slip = sub(vel, ref)
    n = bay.normal_at(t)
    bp = bay.position_at(t)
    closing = -dot(slip, n)
    lateral = norm(sub(slip, scale(n, dot(slip, n))))
    los = unit(sub(pos, bp))
    misalign = math.degrees(math.acos(max(-1.0, min(1.0, dot(los, n)))))
    naive = contact_is_safe(pos, vel, bay, t, max_closing, max_lateral,
                            max_misalign_deg)
    return {
        "safe": (closing <= max_closing and lateral <= max_lateral
                 and misalign <= max_misalign_deg),
        "closing_rate": closing,
        "lateral_slip": lateral,
        "misalignment_deg": misalign,
        "range_m": norm(sub(pos, bp)),
        "naive_safe": naive["safe"],
        "naive_lateral": naive["lateral_drift"],
        "intrinsic_lateral": bay.drum.omega * norm(sub(pos, bp)),
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


# ===========================================================================
# THE ENVELOPE -- what the airframe can and cannot be asked to do
# ===========================================================================

class InfeasibleApproach(Exception):
    """A demanded standoff that no guidance law can fly.

    Raised, never warned about. `starfury_scene.docking_envelope` had this
    arithmetic and printed `feasible: NO` in a table nothing read; a number in
    a report is not a constraint on anything. Here it stops the plan.
    """


def max_formation_radius(omega, max_accel):
    """The radius beyond which omega^2 R exceeds everything the craft has.

    Not a soft limit and not a comfort figure: at this radius the whole
    airframe is spent holding the circle and there is nothing left to steer
    with, and past it the craft simply leaves.
    """
    return max_accel / (omega * omega)


def formation_cost(omega, radius):
    """Sustained acceleration needed to hold a circle of this radius, m/s^2."""
    return omega * omega * radius


# The fraction of maximum thrust the plan refuses to spend on merely staying on
# the circle, so that something is left to correct with. INV-398.
CONTROL_RESERVE = 0.30
# Below this the plan refuses even though omega^2 R is under amax: a craft with
# 2% of its thrust available for control is not docking, it is falling. INV-398.
MIN_RESERVE = 0.05


@dataclass
class ApproachPlan:
    """A flyable docking approach, or an exception instead of one.

    Every field is derived. `standoff_m` comes from the control reserve,
    `closing_rate_m_s` from `contact_is_safe`'s own buffer limit, and the two
    terminal gains from splitting the reserve between the position and velocity
    halves of the tracking error -- which lands on zeta = 0.93 without anyone
    choosing a damping ratio.
    """
    bay: object
    max_accel: float
    omega: float
    standoff_m: float
    hold_radius_m: float
    hold_cost_m_s2: float
    control_reserve: float
    authority_m_s2: float
    closing_rate_m_s: float
    capture_range_m: float
    capture_speed_m_s: float
    vel_gain: float
    cruise_vmax_m_s: float
    brachistochrone_derate: float
    terminal_taper: float
    ceiling_radius_m: float
    contact_standoff_m: float = 0.0
    # A CALLABLE, and it is the hull the player looks at rather than a copy of
    # it. `starfury_scene` passes `components.radius_at(profile, z)` -- the same
    # function `generate_hull` builds the mesh from -- so a guidance law that
    # flies through the station cannot pass by disagreeing with it about where
    # the station is. Hard rule 4, applied to a trajectory.
    #
    # Left None only for `test_docking.py`, which has no hull loaded; the local
    # fallback below then guards a box one bay-radius long around the bay, which
    # is where the bay's own structure is and nothing else.
    hull_radius_at: object = None

    def inside_hull(self, pos):
        r = math.hypot(pos[0], pos[1])
        if self.hull_radius_at is not None:
            return r < self.hull_radius_at(pos[2])
        return (r < self.bay.radius - self.capture_range_m
                and abs(pos[2] - self.bay.z) < self.bay.radius)

    @property
    def effective_kp(self):
        """What the law's stiffness works out to, for the record. The position
        error only ever reaches the command through the velocity cap, so the
        stiffness is the taper times the one gain rather than a second knob."""
        return self.terminal_taper * self.vel_gain

    @property
    def effective_zeta(self):
        return 0.5 * self.vel_gain / math.sqrt(self.effective_kp)

    def target(self, t, standoff, closing=0.0):
        """Position, velocity and acceleration of a point held `standoff` off
        the bay while closing on it at `closing` m/s.

        Differentiated rather than guessed. With p = R(t) n(t), R' = -closing
        and n' = omega * tangent:

            v = -closing n + omega R t
            a = -omega^2 R n - 2 closing omega t

        The second term of the acceleration is the one a careless port drops:
        it is the Coriolis term of a radial closure, 0.56 m/s^2 at the plan's
        own closing rate, and without it the craft arrives tangentially adrift.
        """
        b = self.bay
        ang = b.angle_at(t)
        n = (math.cos(ang), math.sin(ang), 0.0)
        tg = (-math.sin(ang), math.cos(ang), 0.0)
        R = b.radius + standoff
        p = (R * n[0], R * n[1], b.z)
        v = add(scale(tg, self.omega * R), scale(n, -closing))
        acc = add(scale(n, -self.omega * self.omega * R),
                  scale(tg, -2.0 * closing * self.omega))
        return p, v, acc


def plan_approach(bay, max_accel, standoff=None, reserve=CONTROL_RESERVE,
                  craft_half_length_m=0.0):
    """Build a plan, or refuse.

    `standoff=None` derives the hold point from the reserve, which is the
    normal path. Passing one explicitly is how a caller asks for something the
    airframe may not be able to do -- and how the negative control asks for
    something it certainly cannot.
    """
    omega = bay.drum.omega
    ceiling = max_formation_radius(omega, max_accel)
    if standoff is None:
        standoff = ceiling * (1.0 - reserve) - bay.radius
        if standoff <= 0.0:
            raise InfeasibleApproach(
                f"the bay itself is at r {bay.radius:.1f} m and the ceiling is "
                f"{ceiling:.1f} m: holding station AT the bay already costs "
                f"{formation_cost(omega, bay.radius) / max_accel:.1%} of thrust")
    R = bay.radius + standoff
    cost = formation_cost(omega, R)
    if cost >= max_accel:
        raise InfeasibleApproach(
            f"standoff {standoff:.1f} m puts the hold point at r {R:.1f} m, "
            f"past the {ceiling - bay.radius:.1f} m ceiling: omega^2 R = "
            f"{cost:.2f} m/s^2 against {max_accel:.2f} available "
            f"({cost / max_accel:.1%}). No guidance law helps")
    have = 1.0 - cost / max_accel
    if have < MIN_RESERVE:
        raise InfeasibleApproach(
            f"standoff {standoff:.1f} m is inside the ceiling but leaves "
            f"{have:.1%} of thrust for control, under the {MIN_RESERVE:.0%} "
            f"floor: the craft could hold the circle and could not steer on it")

    authority = have * max_accel
    # The buffer limit `contact_is_safe` already enforces, with a quarter of it
    # kept back so a plan flown perfectly is not sitting on its own gate.
    closing = 2.0 * 0.75
    # Capture: how near the hold point the craft has to be, and how nearly
    # matched, before the standoff ramp starts. INV-399.
    capture_range, capture_speed = 20.0, 4.0
    # 0.15/s of taper puts the commanded closing speed at 3 m/s when the range
    # is `capture_range`, i.e. inside `capture_speed`, so the capture test can
    # be met rather than approached forever.
    taper = 0.15
    # THE ONE GAIN, AND IT IS SOLVED RATHER THAN TUNED. The law's whole output
    # above the feedforward is `vel_gain * (v_desired - v)`, so the worst state
    # the capture test still admits -- `capture_range` of position error and
    # `capture_speed` of velocity error -- must cost exactly the authority the
    # reserve bought and not a newton more:
    #
    #     vel_gain * (taper * capture_range + capture_speed) = authority
    #
    # Damping is then whatever that implies (zeta 1.15, overdamped) rather than
    # a number anybody picked.
    vel_gain = authority / (taper * capture_range + capture_speed)
    return ApproachPlan(
        bay=bay, max_accel=max_accel, omega=omega, standoff_m=standoff,
        hold_radius_m=R, hold_cost_m_s2=cost, control_reserve=have,
        authority_m_s2=authority, closing_rate_m_s=closing,
        capture_range_m=capture_range, capture_speed_m_s=capture_speed,
        vel_gain=vel_gain,
        # The velocity cap's three terms, each for a different reason. The
        # cruise is starfury.gd's own TRANSIT_VMAX; the square-root term is the
        # brachistochrone derated so half the airframe is left for steering; the
        # linear taper is what stops the terminal hunting.
        cruise_vmax_m_s=520.0, brachistochrone_derate=0.5, terminal_taper=taper,
        ceiling_radius_m=ceiling,
        # WHERE THE RAMP STOPS, and it stops at the craft's own half-length
        # rather than at zero. Two reasons, and the second is the one that
        # matters. The physical one: a fighter's CENTRE cannot reach the bay's
        # reference point, its NOSE does, and half a length is where that is.
        # The measurement one: `contact_is_safe`'s misalignment term is the
        # angle of `unit(craft - bay)`, which is undefined as that vector goes
        # to zero -- `unit()` returns (0,0,0), the dot product is 0, and the
        # test reports exactly 90 degrees of misalignment however perfect the
        # dock. A safety gate that reads 90 at zero range is a gate that can
        # never pass, and it would have been read as a docking failure.
        contact_standoff_m=craft_half_length_m)


# ===========================================================================
# THE LAW
# ===========================================================================

def _clip(v, cap):
    n = norm(v)
    return v if n <= cap else scale(v, cap / n)


def loiter_point(plan, pos):
    """Where the craft waits for the bay, and why waiting is the right answer.

    THE STATION CANNOT BE CHASED AND DOES NOT NEED TO BE. A point on the hold
    circle is doing 68.5 m/s and costs 12.9 m/s^2 to stay on; a point FIXED IN
    INERTIAL SPACE on the same circle costs nothing at all, and the bay arrives
    at it within one 33.47 s rotation whatever the craft does. So the approach
    is: stop on the circle, wait, and spin up as the bay comes round. That is
    the launch run backwards -- the launch is a craft at rest in the ROTATING
    frame being thrown clear, the dock is a craft at rest in the INERTIAL frame
    being caught.

    The azimuth is the craft's OWN, not the bay's, and that is a hull-clearance
    result rather than a preference. Measured along the straight line from the
    look-back point where the mission's transit ends: aiming at the hold point
    at the bay's phase clears the hull by **-11.6 m at z 6888** -- it goes
    through the station -- and aiming at the same radius on the craft's own
    azimuth clears by **+96.5 m**, with the tightest point being the loiter
    point itself. One is a docking approach and the other is a collision.
    """
    th = math.atan2(pos[1], pos[0])
    return (plan.hold_radius_m * math.cos(th),
            plan.hold_radius_m * math.sin(th), plan.bay.z)


def commit_lead_angle(plan):
    """How far behind the craft the bay must be before the run-in starts.

    Spin-up time from rest to the hold circle's 68.5 m/s, at the derated
    acceleration the plan already uses for braking, is v_hold / (derate * amax)
    = 7.46 s; the bay covers omega * that = 1.400 rad = 80.2 degrees in the
    time. Committing earlier means chasing the bay across the circle's chord,
    and the chord of an 85 degree gap dips to r = R cos(42.5) = 269 m, which at
    this z IS the hull. The lead angle is therefore a clearance constraint that
    happens to also be the spin-up time.
    """
    v_hold = plan.omega * plan.hold_radius_m
    return plan.omega * v_hold / (plan.brachistochrone_derate * plan.max_accel)


def stage_target(plan, t, stage, standoff, loiter):
    """The point the law is flying at, whichever leg it is on.

    Split out because the GDScript port must resolve the target the same way,
    and a stage machine duplicated as an if-ladder in two languages is the
    shape of drift this project keeps finding.
    """
    if stage in ("return", "loiter"):
        return loiter, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    closing = plan.closing_rate_m_s if stage == "terminal" else 0.0
    return plan.target(t, standoff, closing)


def dock_command(plan, t, pos, vel, standoff, closing=0.0, phase_match=True,
                 target=None):
    """The whole guidance law. One function, one gain, two feedforwards.

        a = a_target(t) + vel_gain * (v_desired - v)
        v_desired = unit(target - pos) * vcap + v_target(t)

    VELOCITY MATCHING, NOT PURSUIT, for the reason `starfury.gd`'s transit leg
    records: a closing-rate test cannot see LATERAL velocity, and at 400 m/s
    lateral drift is most of the miss. Aiming at `v_desired - v` kills the
    lateral component for free because it is part of the error rather than
    invisible to it.

    AND THE TARGET'S OWN ACCELERATION IS FED FORWARD, which is the thing the
    first version of this law did not do and could not converge without. With
    velocity matching alone the equilibrium is *wrong*: sitting exactly on the
    hold point with exactly the hold point's velocity gives zero command, and
    the craft then flies straight while the hold point curves away. Measured,
    that law settled 235 m short with the throttle pinned at 1.00 for all 48,001
    steps and ended INSIDE the bay circle at r 173 m. With the feedforward the
    equilibrium is the circle itself: v = v_target gives a = a_target, which is
    the 12.86 m/s^2 of centripetal the hold radius costs.

    The feedforward is NOT spurious at long range even though it points at the
    station: the velocity term is then hundreds of m/s^2 before clipping and
    tilts the result by under 3%.

    `phase_match=False` is the negative control. It drops the target's velocity
    and acceleration -- docking with a rotating station as though it were not
    rotating -- and the craft misses by a stated distance.

    Returns `(accel_world, range_m, velocity_error_m_s)`.
    """
    p, v, a = target if target is not None else plan.target(t, standoff, closing)
    if not phase_match:
        v = (0.0, 0.0, 0.0)
        a = (0.0, 0.0, 0.0)
    dp = sub(p, pos)
    d = norm(dp)
    # THE BRACHISTOCHRONE TERM HAS NO STANDOFF SUBTRACTED FROM IT, and that is
    # the whole reason this law converges. `starfury.gd`'s transit leg uses
    # `sqrt(2 * 0.7 * amax * (d - 100))` because it is aiming at a waypoint it
    # means to stop short of. Copied here with `- capture_range` it read zero
    # for every d under 20 m, which took the WHOLE velocity cap to zero (it is
    # a min), which removed the position feedback entirely -- and a law with no
    # position term has a perfect equilibrium at any offset whose velocity
    # matches. Measured: the craft settled 14.26 m from the bay and held it for
    # 160 s with the relative speed at 0.0097 m/s and the commanded z
    # acceleration identically 0.0000, so a 3.96 m axial error could never be
    # corrected. It looked like a tracking lag and it was a missing term.
    #
    # The two caps cross at 817 m: the taper governs the terminal approach and
    # the brachistochrone the run in.
    vcap = min(plan.cruise_vmax_m_s,
               math.sqrt(2.0 * plan.brachistochrone_derate * plan.max_accel * d),
               plan.terminal_taper * d)
    v_des = add(scale(unit(dp), vcap), v)
    cmd = add(a, scale(sub(v_des, vel), plan.vel_gain))
    return _clip(cmd, plan.max_accel), d, norm(sub(v, vel))


# ===========================================================================
# THE AUTOPILOT -- deliberately duplicated in godot/scripts/starfury.gd
# ===========================================================================

# Attitude loop gains. Proportional on the pointing error, derivative on the
# rate error -- and the rate is measured against the FEEDFORWARD, not against
# zero. INV-400.
ATT_KP, ATT_KD = 0.9, 2.2
# Above this pointing error the mains are shut: thrust 40 degrees off the demand
# is not a weaker correction, it is a different one. INV-401.
THRUST_GATE_DEG = 25.0


def attitude_command(ship, aim, omega_ff=(0.0, 0.0, 0.0), throttle=1.0):
    """Point the nose at `aim`, tracking a demand that is itself rotating.

    THE FEEDFORWARD IS NOT POLISH, IT IS THE DIFFERENCE BETWEEN DOCKING AND NOT.
    A docking craft's thrust vector rotates with the station: 0.1877 rad/s,
    10.75 deg/s, once round every 33.47 s. A pure PD tracking that settles where
    `kp * error = kd * rate`, i.e. at a standing error of kd/kp * omega = 0.46
    rad = 26 degrees -- past the thrust gate, so the mains never light and the
    craft never docks. Handing the loop the station's own omega moves the
    equilibrium to zero error, and it is the one number that does it.

    `rot.z` is zeroed because the layout HAS no roll authority: every RCS
    thruster fires through the centre of mass and the four mains sit on the aft
    centreline of their booms, so they torque about X and Y and not about Z.
    """
    f = ship.forward
    axis = cross(f, aim)
    ang = math.atan2(norm(axis), dot(f, aim))
    err = (0.0, 0.0, 0.0)
    if norm(axis) > 1e-12:
        err = scale(ship.world_to_body(unit(axis)), ang)
    w_ff = ship.world_to_body(omega_ff)
    rot = sub(scale(err, ATT_KP), scale(sub(ship.angular_velocity, w_ff), ATT_KD))
    rot = (rot[0], rot[1], 0.0)
    if norm(rot) > 1.0:
        rot = unit(rot)
    thr = throttle if ang < math.radians(THRUST_GATE_DEG) else 0.0
    return ship.allocate((0.0, 0.0, thr), rot), math.degrees(ang)


# ===========================================================================
# THE FLIGHT
# ===========================================================================

@dataclass
class DockRun:
    """What a docking approach did, in the numbers a pilot would read."""
    docked: bool = False
    reason: str = ""
    elapsed_s: float = 0.0
    return_s: float = 0.0
    loiter_s: float = 0.0
    run_in_s: float = 0.0
    terminal_s: float = 0.0
    settle_s: float = 0.0
    loiter_point_m: list = field(default_factory=list)
    commit_lead_deg: float = 0.0
    closing_rate_m_s: float = 0.0
    lateral_slip_m_s: float = 0.0
    naive_lateral_m_s: float = 0.0
    naive_safe: bool = False
    lateral_offset_m: float = 0.0
    misalignment_deg: float = 0.0
    phase_error_deg: float = 0.0
    contact_speed_m_s: float = 0.0
    contact_radius_m: float = 0.0
    radial_velocity_m_s: float = 0.0
    peak_accel_m_s2: float = 0.0
    peak_accel_fraction: float = 0.0
    dock_peak_accel_m_s2: float = 0.0
    dock_peak_accel_fraction: float = 0.0
    saturated_steps: int = 0
    steps: int = 0
    miss_m: float = 0.0
    closest_m: float = 0.0
    hull_clearance_m: float = float("inf")
    contact_safe: bool = False
    samples: list = field(default_factory=list)


def fly(plan, ship, t0=0.0, dt=1.0 / 120.0, max_s=400.0, phase_match=True,
        sample_every=60):
    """Fly the whole approach with the real rigid body and the real allocator.

    NOT AN ACCELERATION INTEGRATOR. The command comes out of the guidance law as
    a world-frame acceleration, the attitude loop points the nose at it, and the
    thrust that actually arrives is whatever eleven thrusters and one clamped
    allocator produce -- which is less than was asked for, at an angle, and is
    the honest answer. A guidance study that integrates the commanded vector
    directly proves the law converges and says nothing about whether the craft
    can fly it.

    Returns a `DockRun`. `docked=False` with a `reason` is a normal outcome and
    the negative control depends on it.
    """
    bay = plan.bay
    t = t0
    stage = "return"
    standoff = plan.standoff_m
    out = DockRun()
    closest = float("inf")
    t_stage = t0
    prev_aim = None
    loiter = loiter_point(plan, ship.position)
    lead = commit_lead_angle(plan)
    armed = False
    out.loiter_point_m = list(loiter)
    out.commit_lead_deg = math.degrees(lead)
    while t - t0 < max_s:
        target = stage_target(plan, t, stage, standoff, loiter)
        cmd, d, dv = dock_command(plan, t, ship.position, ship.velocity,
                                  standoff, 0.0, phase_match, target)
        bp = bay.position_at(t)
        closest = min(closest, norm(sub(ship.position, bp)))
        if stage in ("return", "loiter"):
            if stage == "return" and d <= plan.capture_range_m \
                    and dv <= plan.capture_speed_m_s:
                stage = "loiter"
                out.return_s = t - t_stage
                t_stage = t
            if stage == "loiter":
                # The bay must be BEHIND the craft by EXACTLY the spin-up arc,
                # which means catching the gap on its way DOWN through `lead`
                # and not merely finding it below.
                #
                # THIS IS A REAL DEFECT THE SWEEP CAUGHT. The first version
                # committed whenever `gap <= lead`, and on one of twelve start
                # phases the craft arrived at the loiter point with the bay 3
                # degrees away. It committed instantly, the bay -- doing 55 m/s
                # against a craft at rest -- swept straight past, the gap
                # wrapped to 357 degrees, and the law then chased it the long
                # way round and cut the chord to r 258.3 m, which is 20 m inside
                # the bay circle and at the real station is inside the hull.
                # Arming on `gap > lead` first makes the wait at most one
                # rotation and the commit geometry identical every time.
                gap = (math.atan2(ship.position[1], ship.position[0])
                       - bay.angle_at(t)) % (2.0 * math.pi)
                if gap > lead:
                    armed = True
                if armed and gap <= lead:
                    stage = "run_in"
                    out.loiter_s = t - t_stage
                    t_stage = t
        elif stage == "run_in":
            if d <= plan.capture_range_m and dv <= plan.capture_speed_m_s:
                stage = "terminal"
                out.run_in_s = t - t_stage
                t_stage = t
        elif stage == "terminal":
            standoff = max(plan.contact_standoff_m,
                           standoff - plan.closing_rate_m_s * dt)
            if standoff <= plan.contact_standoff_m:
                stage = "settle"
                out.terminal_s = t - t_stage
                t_stage = t
        else:
            # SETTLE. The ramp is at the contact standoff and the loop is left
            # to close on it. A dock is declared when `contact_report` -- the
            # module's own three-condition test, referenced to the rotating
            # structure -- says the craft could touch, not when a range counter
            # reaches zero.
            if contact_report(bay, t, ship.position, ship.velocity)["safe"] \
                    and d <= plan.capture_range_m:
                out.settle_s = t - t_stage
                out.docked = True
                break
        # THE HULL IS NOT A SUGGESTION. Nothing in this model collides, so a law
        # that flies through the station reports a clean miss distance and looks
        # merely inaccurate. The first version of this law ended at r 173 m --
        # 120 m inside the bay mouth -- and only this check makes that a failure
        # rather than a number.
        #
        # AND THE FIRST VERSION OF THE CHECK WAS ITSELF WRONG, which is worth
        # the line: it tested cylindrical radius alone, so it fired on a craft
        # 675 m BEYOND THE AFT CAP, where there is no station to be inside of.
        # A containment test on a body 8 km long has to consult the body.
        out.hull_clearance_m = min(
            out.hull_clearance_m,
            math.hypot(ship.position[0], ship.position[1])
            - (plan.hull_radius_at(ship.position[2])
               if plan.hull_radius_at is not None else 0.0))
        if plan.inside_hull(ship.position):
            out.reason = (
                f"flew into the hull at r "
                f"{math.hypot(ship.position[0], ship.position[1]):.1f} m, "
                f"z {ship.position[2]:.1f} m")
            break
        mag = norm(cmd)
        out.peak_accel_m_s2 = max(out.peak_accel_m_s2, mag)
        if stage in ("terminal", "settle"):
            # SEPARATELY, because the return leg is full throttle by design and
            # would hide the number that matters. The dock's own peak is what
            # says whether the standoff was chosen inside the envelope.
            out.dock_peak_accel_m_s2 = max(out.dock_peak_accel_m_s2, mag)
        if mag >= plan.max_accel - 1e-9:
            out.saturated_steps += 1
        # THE FEEDFORWARD IS THE DEMAND'S OWN MEASURED ROTATION RATE, not the
        # station's omega. Both are right at the bay and only one is right at
        # 10 km: during the run-in the demand points wherever the velocity error
        # is and rotates at nothing like omega, so feeding omega in there
        # commands a turn nobody asked for. `cross(prev, now) / dt` is the rate
        # the demand is actually turning at, it needs one step of memory and no
        # gain, and it converges to 0.1877 rad/s -- omega, to three figures --
        # by the time the craft is on the circle. Measured with it: the pointing
        # error runs 0.0-0.5 deg for the whole approach. Without it: pinned at
        # exactly 25.0, the thrust gate, because a pure PD tracking a demand
        # that rotates at omega settles at kd/kp * omega = 26 degrees of
        # standing error and the mains then never light.
        aim = unit(cmd)
        ff = (0.0, 0.0, 0.0) if prev_aim is None \
            else scale(cross(prev_aim, aim), 1.0 / dt)
        prev_aim = aim
        throttle = min(1.0, mag / plan.max_accel)
        th, _ang = attitude_command(ship, aim, ff, throttle)
        ship.step(dt, th)
        t += dt
        out.steps += 1
        if out.steps % sample_every == 0:
            out.samples.append({
                "t_s": t, "stage": stage, "standoff_m": standoff,
                "position": list(ship.position), "velocity": list(ship.velocity),
                "accel_cmd_m_s2": mag,
            })
    out.elapsed_s = t - t0
    out.closest_m = closest
    if not out.docked and not out.reason:
        out.reason = (f"ran out of time in stage {stage}; closest approach "
                      f"{closest:.1f} m")
        if stage == "run_in":
            out.terminal_s = 0.0
    bp = bay.position_at(t)
    n = bay.normal_at(t)
    out.miss_m = norm(sub(ship.position, bp))
    safe = contact_report(bay, t, ship.position, ship.velocity)
    out.contact_safe = bool(safe["safe"]) and out.docked
    out.closing_rate_m_s = safe["closing_rate"]
    out.lateral_slip_m_s = safe["lateral_slip"]
    out.naive_lateral_m_s = safe["naive_lateral"]
    out.naive_safe = bool(safe["naive_safe"])
    out.misalignment_deg = safe["misalignment_deg"]
    d = sub(ship.position, bp)
    out.lateral_offset_m = norm(sub(d, scale(n, dot(d, n))))
    out.phase_error_deg = math.degrees(
        math.atan2(ship.position[1], ship.position[0]) - bay.angle_at(t))
    while out.phase_error_deg > 180.0:
        out.phase_error_deg -= 360.0
    while out.phase_error_deg < -180.0:
        out.phase_error_deg += 360.0
    out.contact_speed_m_s = norm(ship.velocity)
    out.contact_radius_m = math.hypot(ship.position[0], ship.position[1])
    out.radial_velocity_m_s = dot(ship.velocity, n)
    out.peak_accel_fraction = out.peak_accel_m_s2 / plan.max_accel
    out.dock_peak_accel_fraction = out.dock_peak_accel_m_s2 / plan.max_accel
    return out


# ===========================================================================
# THE SWEEP -- one dock is an existence proof, and this project does not accept
# those
# ===========================================================================

def sweep(plan, make_ship, start, phases=12, dt=1.0 / 120.0, max_s=400.0,
          phase_match=True):
    """Dock from `phases` start times spread over one rotation of the station.

    ONE SUCCESSFUL DOCK PROVES NOTHING ABOUT A ROTATING TARGET. The bay's phase
    at the moment the approach begins is the single variable the whole problem
    turns on, and a law can dock perfectly from the phase it happened to be
    written against and fly into the hull from the one 90 degrees away. Sweeping
    the start time over `bay.drum.period` is the cheap denominator: it costs one
    run per phase and it is the only evidence here that the law is a law rather
    than a coincidence.

    It also exposes the loiter wait, which is invisible in a single run --
    `loiter_s` came out 0.0 on the first converged flight because the bay was
    already inside the commit lead when the craft arrived.
    """
    period = plan.bay.drum.period
    rows = []
    for i in range(phases):
        t0 = start["t0"] + i * period / phases
        ship = make_ship()
        ship.position = tuple(start["position"])
        ship.velocity = tuple(start["velocity"])
        ship.orientation = tuple(start["orientation"])
        r = fly(plan, ship, t0=t0, dt=dt, max_s=max_s, phase_match=phase_match)
        rows.append((t0, math.degrees(plan.bay.angle_at(t0)) % 360.0, r))
    return rows


# ===========================================================================
# THE GATE
# ===========================================================================

def _load_schema():
    import os
    import yaml
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    return yaml.safe_load(open(os.path.join(root, "station/schema/station.yaml")))


def selftest(phases=12, verbose=True):
    """Everything the guidance law can be checked on without the hull mesh.

    WHY THIS EXISTS WHEN `sdocking` ALREADY RUNS IN CI. It runs
    `test_docking.py`, which tests `DockingBay`, `closing_rate`,
    `contact_is_safe`, `relative_speed`, `spin_match_velocity` and
    `axial_approach_is_trivial` -- every function that existed before this
    session -- and imports but never calls one line of the guidance law. A CI
    step that cannot fail for a defect in the thing it is named after is the
    defect CLAUDE.md names three times, and it was one import away from being
    invisible.

    `starfury_scene.py --dock-gate` is the same law against the REAL hull, the
    REAL cobra bay measured off the mesh, and the airframe's own length. This
    one needs no mesh and runs in two seconds, so it can live beside the
    module it tests.
    """
    from rotating_frame import from_schema
    schema = _load_schema()
    drum = from_schema(schema)
    ship = Starfury()
    amax = ship.max_linear_accel()
    # The habitat floor's own radius, so this test needs nothing measured off a
    # mesh. `starfury_scene.py --dock-gate` runs the same law at the real cobra
    # bay radius, which is 293.78 m and further out.
    bay = DockingBay(drum, drum.floor_radius, 5400.0, 0.3)
    ok = True
    lines = []

    def row(name, good, detail=""):
        nonlocal ok
        ok = ok and good
        lines.append(f"  {'PASS' if good else 'FAIL'}  {name}"
                     + (f"  -- {detail}" if detail else ""))

    # --- the envelope --------------------------------------------------------
    ceiling = max_formation_radius(drum.omega, amax)
    row("the ceiling is amax / omega^2",
        abs(formation_cost(drum.omega, ceiling) - amax) < 1e-9,
        f"{ceiling:.1f} m of radius, {ceiling - bay.radius:.1f} m of standoff")
    for demand, why in ((ceiling - bay.radius + 50.0, "past the ceiling"),
                        (ceiling - bay.radius - 1.0, "inside it, no authority")):
        try:
            plan_approach(bay, amax, standoff=demand)
            row(f"a standoff {why} is refused", False, "IT WAS ACCEPTED")
        except InfeasibleApproach as e:
            row(f"a standoff {why} is refused", True, str(e)[:96])

    plan = plan_approach(bay, amax, craft_half_length_m=3.0)
    row("the derived hold point is inside the ceiling with reserve left",
        plan.control_reserve >= MIN_RESERVE and plan.hold_radius_m < ceiling,
        f"standoff {plan.standoff_m:.1f} m, hold cost "
        f"{plan.hold_cost_m_s2:.2f} m/s^2, {plan.control_reserve:.1%} in hand")

    # --- the target's own kinematics, differentiated numerically -------------
    # The feedforward IS the law; if `target` is wrong the rest cannot save it.
    # DIFFERENTIATED ALONG THE RAMP, not at a frozen standoff. The first
    # version of this check held `standoff` constant across the three samples
    # and failed by exactly 1.500 m/s -- the closing rate -- because `target`'s
    # velocity carries the -closing*n term the frozen samples cannot show. The
    # test was wrong and the law was right, and the size of the miss named which.
    h = 1e-4
    c = plan.closing_rate_m_s
    worst_v = worst_a = 0.0
    for t in (0.0, 3.3, 17.0, 31.4):
        p0, v0, _a0 = plan.target(t - h, 12.0 + c * h, c)
        p2, v2, _a2 = plan.target(t + h, 12.0 - c * h, c)
        _p1, v1, a1 = plan.target(t, 12.0, c)
        worst_v = max(worst_v, norm(sub(scale(sub(p2, p0), 0.5 / h), v1)))
        worst_a = max(worst_a, norm(sub(scale(sub(v2, v0), 0.5 / h), a1)))
    row("target velocity is the derivative of target position",
        worst_v < 1e-5, f"worst |d/dt p - v| = {worst_v:.3e} m/s")
    row("target acceleration is the derivative of target velocity",
        worst_a < 1e-5, f"worst |d/dt v - a| = {worst_a:.3e} m/s^2  "
        f"(this is the 2*closing*omega Coriolis term)")

    # --- the flight ----------------------------------------------------------
    start = {"t0": 0.0,
             # 4 km out on a clear azimuth, at rest: far enough that the run in
             # is a real flight and near enough that this stays a two-second
             # test.
             "position": (-3000.0, 2600.0, 3000.0), "velocity": (0.0, 0.0, 0.0),
             "orientation": (1.0, 0.0, 0.0, 0.0)}
    rows = sweep(plan, Starfury, start, phases=phases)
    docked = [r for _t, _a, r in rows if r.docked]
    lines.append(f"  ..    docked from {len(docked)} of {len(rows)} start "
                 f"phases over one {drum.period:.2f} s rotation")
    for t0, ang, r in rows:
        lines.append(
            f"        bay at {ang:6.1f} deg: "
            + (f"DOCK in {r.elapsed_s:6.1f} s  (return {r.return_s:5.1f} "
               f"loiter {r.loiter_s:5.1f} run-in {r.run_in_s:5.1f} "
               f"close {r.terminal_s:5.1f} settle {r.settle_s:5.2f})  "
               f"closing {r.closing_rate_m_s:5.3f} slip {r.lateral_slip_m_s:6.4f} "
               f"miss {r.miss_m:5.2f} peak {r.dock_peak_accel_fraction:5.1%}"
               if r.docked else f"NO DOCK -- {r.reason}"))
    row("every start phase docks", len(docked) == len(rows),
        f"{len(docked)}/{len(rows)}")
    if docked:
        row("no dock exceeds the airframe",
            all(r.dock_peak_accel_fraction <= 1.0 for r in docked),
            f"worst {max(r.dock_peak_accel_fraction for r in docked):.1%} of max")
        row("every contact is inside the safety envelope",
            all(r.contact_safe for r in docked))
        row("the loiter wait is used and bounded by one rotation",
            all(r.loiter_s <= drum.period + 1e-6 for r in docked),
            f"longest {max(r.loiter_s for r in docked):.1f} s of "
            f"{drum.period:.2f} s")

    # --- NEGATIVE CONTROL: no phase matching --------------------------------
    bad = sweep(plan, Starfury, start, phases=4, phase_match=False)
    misses = [r.miss_m for _t, _a, r in bad]
    row("CONTROL: with phase matching nulled, nothing docks",
        not any(r.docked for _t, _a, r in bad),
        f"misses {', '.join(f'{m:.0f}' for m in misses)} m "
        f"(median {sorted(misses)[len(misses) // 2]:.0f} m) against "
        f"{sum(r.miss_m for _t, _a, r in rows if r.docked) / max(1, len(docked)):.2f} m docked")

    if verbose:
        print("--- the docking guidance law, at the habitat floor radius ---")
        print("\n".join(lines))
        print("DOCKING SELFTEST: " + ("PASS" if ok else "FAIL"))
    return ok, rows


if __name__ == "__main__":
    import sys as _sys
    _ok, _ = selftest()
    _sys.exit(0 if _ok else 1)
