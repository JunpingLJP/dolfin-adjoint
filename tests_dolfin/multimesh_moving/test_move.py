import os
from dolfin import *
from dolfin_adjoint import *

class Dirichlet(SubDomain):
    def inside(self, x, on_boundary):
        return on_boundary

class Propeller(SubDomain):
    def inside(self, x, on_boundary):
        return (on_boundary and ((x[0]-5)**2+(x[1]-5)**2)<2)

def test_move():
    path = os.path.dirname(__file__)
    mesh_0 = Mesh(os.path.join(path, "propeller_background.xml.gz"))
    mesh_1 = Mesh(os.path.join(path, "propeller_front.xml.gz"))
    multimesh = MultiMesh()
    multimesh.add(mesh_0)
    multimesh.add(mesh_1)
    multimesh.build()
    # Define functionspace
    V = MultiMeshFunctionSpace(multimesh, "Lagrange", 1)

    # Time parameters and init condition
    dt = Constant(0.01)
    t = float(dt)
    T = 0.03
    g = Constant(1)
    u0 = project(g, V, name="u0", annotate=False)

    # Initial guess
    f = MultiMeshFunction(V, name="f")

    # Define trial and test functions and right-hand side
    u = TrialFunction(V)
    v = TestFunction(V)

    # Define facet normal and mesh size
    n = FacetNormal(multimesh)
    h = 2.0*Circumradius(multimesh)
    h = (h('+') + h('-')) / 2

    # Set parameters
    alpha = 4.0
    beta = 4.0

    # Define bilinear form
    a = u*v*dX + dt* ( inner(grad(u), grad(v))*dX \
        - dot(avg(grad(u)), jump(v, n))*dI \
        - dot(avg(grad(v)), jump(u, n))*dI \
        + alpha/h*jump(u)*jump(v)*dI \
        + beta*dot(jump(grad(u)), jump(grad(v)))*dO )

    # Define linear form
    L = u0*v*dX + dt*f*v*dX

    # Assemble linear system
    A = assemble_multimesh(a)
    b = assemble_multimesh(L)

    # Initialize boundary conditions
    bound = Dirichlet()
    bc0 = MultiMeshDirichletBC(V, g, bound)
    # Boundary on propeller
    propfunc = FacetFunction("size_t", mesh_1)
    prop = Propeller()
    propfunc.set_all(0)
    prop.mark(propfunc,1)
    bc1 = MultiMeshDirichletBC(V, Constant(1), propfunc, 1, 1)

    # Solving linear system
    u1 = MultiMeshFunction(V, name="u1")
    adj_start_timestep(time=t)
    while (t <= T):

        b = assemble_multimesh(L)
        bc0.apply(A, b)
        bc1.apply(A, b)
        solve(A, u1.vector(), b)
        u0.assign(u1)
        t += float(dt)

        # Updating mesh
        if (t<=T):
            mesh_1.rotate(90*float(dt))
            multimesh.build()
            A = assemble_multimesh(a)

        adj_inc_timestep(time=t, finished=t>T)

    J = Functional(u1**2*dX)
    m = [Control(u0), Control(f)]

    rf = ReducedFunctional(J, m)
    order = rf.taylor_test([u0, f])
    assert order > 1.8


if __name__ == '__main__':
    test_move()
