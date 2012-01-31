import libadjoint
import ufl
import dolfin
import hashlib

import solving

class FinalFunctional(libadjoint.Functional):
  '''This class implements the libadjoint.Functional abstract base class for the Dolfin adjoint.
  It takes in a form that evaluates the functional at the final timestep, and implements the 
  necessary routines such as calling the functional  and taking its derivative.'''

  def __init__(self, form):

    self.form = form
    self.activated = False

  def __call__(self, dependencies, values):

    dolfin_dependencies=[dep for dep in ufl.algorithms.extract_coefficients(self.form) if hasattr(dep, "function_space")]

    dolfin_values=[val.data for val in values]

    return dolfin.assemble(dolfin.replace(self.form, dict(zip(dolfin_dependencies, dolfin_values))))

  def derivative(self, variable, dependencies, values):

    # Find the dolfin Function corresponding to variable.
    dolfin_variable = values[dependencies.index(variable)].data

    dolfin_dependencies = [dep for dep in ufl.algorithms.extract_coefficients(self.form) if hasattr(dep, "function_space")]

    dolfin_values = [val.data for val in values]

    current_form = dolfin.replace(self.form, dict(zip(dolfin_dependencies, dolfin_values)))
    test = dolfin.TestFunction(dolfin_variable.function_space())

    return solving.Vector(dolfin.derivative(current_form, dolfin_variable, test))

  def dependencies(self, adjointer, timestep):

    if self.activated is False:
      deps = [solving.adj_variables[coeff] for coeff in ufl.algorithms.extract_coefficients(self.form) if hasattr(coeff, "function_space")]      
      self.activated = True
    else:
      deps = []
    
    return deps

  def __str__(self):
    
    return hashlib.md5(str(self.form)).hexdigest()


class TimeFunctional(libadjoint.Functional):
  '''This class implements the libadjoint.Functional abstract base class for the Dolfin adjoint
  for implementing functionals:
      \int_{T} form dt + finalform(T)
  The two forms, form and finalform, may only use variables of the same timelevel. 
  If finalform is not provided, the second term is neglected.'''

  def __init__(self, form):

    self.form = form

  def __call__(self, timestep, dependencies, values):

    dolfin_dependencies_form = [dep for dep in ufl.algorithms.extract_coefficients(self.form) if hasattr(dep, "function_space")]
    dolfin_values = [val.data for val in values]

    # Check if the functional is to be evaluated at the last timestep
    return dolfin.assemble(dolfin.replace(self.form, dict(zip(dolfin_dependencies, dolfin_values))))

  def derivative(self, variable, dependencies, values):

    # Find the dolfin Function corresponding to variable.
    dolfin_variable = values[dependencies.index(variable)].data

    dolfin_dependencies_form = [dep for dep in ufl.algorithms.extract_coefficients(self.form) if hasattr(dep, "function_space")]
    dolfin_values = [val.data for val in values]

    test = dolfin.TestFunction(dolfin_variable.function_space())
    current_form = dolfin.replace(self.form, dict(zip(dolfin_dependencies_form, dolfin_values)))

    return solving.Vector(dolfin.derivative(current_form, dolfin_variable, test))

  def dependencies(self, adjointer, timestep):
    deps = [solving.adj_variables[coeff] for coeff in ufl.algorithms.extract_coefficients(self.form) if hasattr(coeff, "function_space")]
    # Set the time level of the dependencies:
    for i in range(len(deps)):
      deps[i].var.timestep = timestep
      deps[i].var.iteration = deps[i].iteration_count(adjointer) - 1 

    return deps

  def __str__(self):
    
    return hashlib.md5(str(self.form)).hexdigest()
