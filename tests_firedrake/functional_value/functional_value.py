from __future__ import print_function
from firedrake import *
from firedrake_adjoint import *

mesh = UnitSquareMesh(50, 50)
V = FunctionSpace(mesh, "CG", 1)

def main(ic, annotate=False):
    u_prev = ic.copy(deepcopy=True, name="Temperature")
    u_next = ic.copy(deepcopy=True, name="TemperatureNext")
    u_mid  = Constant(0.5)*u_prev + Constant(0.5)*u_next

    dt = 0.001
    T = 0.003
    t = 0.0

    v = TestFunction(V)

    states = [ic.copy(deepcopy=True)]
    times  = [float(t)]

    if annotate: adj_start_timestep(time=t)
    timestep = 0

    while t < T:
        print("Solving for t == %s" % (t + dt))
        F = inner((u_next - u_prev)/Constant(dt), v)*dx + inner(grad(u_mid), grad(v))*dx
        solve(F == 0, u_next, J=derivative(F, u_next), annotate=annotate)
        u_prev.assign(u_next, annotate=annotate)

        t += dt
        timestep += 1
        states.append(u_next.copy(deepcopy=True, name="TemperatureT%s" % timestep, annotate=False))
        times.append(float(t))

        if annotate: adj_inc_timestep(time=t, finished=t>=T)

    return (times, states, u_prev)

if __name__ == "__main__":
    true_ic = interpolate(Expression("sin(2*pi*x[0])*sin(2*pi*x[1])", degree=1), V)
    (times, true_states, u) = main(true_ic, annotate=False)

    guess_ic = interpolate(Expression("15 * x[0] * (1 - x[0]) * x[1] * (1 - x[1])", degree=4), V)
    (times, computed_states, u) = main(guess_ic, annotate=True)

    success = replay_dolfin(tol=0.0, stop=True)
    assert success

    data = true_states[-1].copy(deepcopy=True, annotate=False)
    combined = zip(times, true_states, computed_states)
    J_orig = assemble(inner(u - data, u - data)*dx)
    print("Base functional value: ", J_orig)

    J = Functional(inner(u - data, u - data)*dx*dt[FINISH_TIME])
    m = FunctionControl("Temperature")
    rf = ReducedFunctional(J, m)

    print("rf(guess_ic): ", rf(guess_ic))
    assert rf(guess_ic) == J_orig
