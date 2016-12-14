from firedrake import *
from firedrake_adjoint import *

def test_register_interpolate():
    mesh = UnitIntervalMesh(10)
    V = FunctionSpace(mesh, "CG", 1)
    f = interpolate(Constant(1), V, annotate=False)
    assert adjointer.adjointer.nequations == 0 

    f = interpolate(Constant(1), V, annotate=True)
    assert adjointer.adjointer.nequations == 1 
    adj_html("forward.html", "forward")
