"""This demo solves the Stokes equations using an iterative linear solver.
Note that the sign for the pressure has been flipped for symmetry."""

# Copyright (C) 2010 Garth N. Wells
#
# This file is part of DOLFIN.
#
# DOLFIN is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DOLFIN is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with DOLFIN. If not, see <http://www.gnu.org/licenses/>.
#
# First added:  2010-08-08
# Last changed: 2010-08-08

# Begin demo

import sys

from dolfin import *
from dolfin_adjoint import *

import numpy; numpy.set_printoptions(threshold=float('nan'))

# Test for PETSc or Epetra
if not has_linear_algebra_backend("PETSc") and not has_linear_algebra_backend("Epetra"):
    info_red("DOLFIN has not been configured with Trilinos or PETSc. Exiting.")
    sys.exit(0)

# Load mesh
mesh = UnitCubeMesh(4, 4, 4)

# Define function spaces
cg2 = VectorElement("CG", tetrahedron, 2)
cg1 = FiniteElement("CG", tetrahedron, 1)
ele = MixedElement([cg2, cg1])
W = FunctionSpace(mesh, ele)

# Boundaries
def right(x, on_boundary): return x[0] > (1.0 - DOLFIN_EPS)
def left(x, on_boundary): return x[0] < DOLFIN_EPS
def top_bottom(x, on_boundary):
    return x[1] > 1.0 - DOLFIN_EPS or x[1] < DOLFIN_EPS

# No-slip boundary condition for velocity
noslip = Constant((0.0, 0.0, 0.0))
bc0 = DirichletBC(W.sub(0), noslip, top_bottom)

# Inflow boundary condition for velocity
inflow = Expression(("-sin(x[1]*pi)", "0.0", "0.0"), degree=2)
bc1 = DirichletBC(W.sub(0), inflow, right)

# Boundary condition for pressure at outflow
zero = Constant(0)
bc2 = DirichletBC(W.sub(1), zero, left)

# Collect boundary conditions
bcs = [bc0, bc1, bc2]

# Define variational problem
(u, p) = TrialFunctions(W)
(v, q) = TestFunctions(W)
f = Constant((0.0, 0.0, 0.0))
a = inner(grad(u), grad(v))*dx + div(v)*p*dx + q*div(u)*dx
L = inner(f, v)*dx

# Form for use in constructing preconditioner matrix
b = inner(grad(u), grad(v))*dx + p*q*dx

# Assemble system
A, bb = assemble_system(a, L, bcs)

# Assemble preconditioner system
P, btmp = assemble_system(b, L, bcs)

# Create Krylov solver and AMG preconditioner
solver = LinearSolver(mpi_comm_world(), "tfqmr", "amg")

# Associate operator (A) and preconditioner matrix (P)
solver.set_operators(A, P)

# Solve
U = Function(W)
U.vector()[:] = 1.0
#solver.parameters["monitor_convergence"] = True
solver.parameters["relative_tolerance"] = 1.0e-14
solver.parameters["absolute_tolerance"] = 1.0e-12
solver.parameters["nonzero_initial_guess"] = True
solver.solve(U.vector(), bb)

assert adjglobals.adjointer.equation_count > 0
assert replay_dolfin(tol=5.0e-9)
