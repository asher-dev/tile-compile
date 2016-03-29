import time
import functools

'''Constraint Satisfaction Routines
   A) class Variable

      This class allows one to define CSP variables.

      On initialization the variable object can be given a name, and
      an original domain of values. This list of domain values can be
      added but NOT deleted from.
      
      To support constraint propagation, the class also maintains a
      set of flags to indicate if a value is still in its current domain.
      So one can remove values, add them back, and query if they are 
      still current. 

    B) class constraint

      This class allows one to define constraints specified by tables
      of satisfying assignments.

      On initialization the variables the constraint is over is
      specified (i.e. the scope of the constraint). This must be an
      ORDERED list of variables. This list of variables cannot be
      changed once the constraint object is created.

      Once initialized the constraint can be incrementally initialized
      with a list of satisfying tuples. Each tuple specifies a value
      for each variable in the constraint (in the same ORDER as the
      variables of the constraint were specified).

    C) Backtracking routine---takes propagator and CSP as arguments
       so that basic backtracking, forward-checking or GAC can be 
       executed depending on the propagator used.

'''


class Variable: 

    '''Class for defining CSP variables.  On initialization the
       variable object should be given a name, and optionally a list of
       domain values. Later on more domain values an be added...but
       domain values can never be removed.

       The variable object offers two types of functionality to support
       search. 
       (a) It has a current domain, implimented as a set of flags 
           determining which domain values are "current", i.e., unpruned.
           - you can prune a value, and restore it.
           - you can obtain a list of values in the current domain, or count
             how many are still there

       (b) You can assign and unassign a value to the variable.
           The assigned value must be from the variable domain, and
           you cannot assign to an already assigned variable.

           You can get the assigned value e.g., to find the solution after
           search.
           
           Assignments and current domain interact at the external interface
           level. Assignments do not affect the internal state of the current domain 
           so as not to interact with value pruning and restoring during search. 

           But conceptually when a variable is assigned it only has
           the assigned value in its current domain (viewing it this
           way makes implementing the propagators easier). Hence, when
           the variable is assigned, the 'cur_domain' returns the
           assigned value as the sole member of the current domain,
           and 'in_cur_domain' returns True only for the assigned
           value. However, the internal state of the current domain
           flags are not changed so that pruning and unpruning can
           work independently of assignment and unassignment. 
           '''
    #
    #set up and info methods
    #
    def __init__(self, name, domain=[]):
        """
        Create a variable object, specifying its name (a string).
        Optionally specify the initial domain.

        :param name: Variable name
        :type name: str
        :param domain: Optional domain of CSP
        :type domain: iterable
        :return: None
        """
        self.name = name                #text name for variable
        self.dom = list(domain)         #Make a copy of passed domain
        self.curdom = [True] * len(domain)      #using list
        #for bt_search
        self.assignedValue = None

    def add_domain_values(self, values):
        '''Add additional domain values to the domain
           Removals not supported removals'''
        for val in values: 
            self.dom.append(val)
            self.curdom.append(True)

    def domain_size(self):
        '''Return the size of the (permanent) domain'''
        return(len(self.dom))

    def domain(self):
        '''return the variable's (permanent) domain'''
        return(list(self.dom))

    #
    #methods for current domain (pruning and unpruning)
    #

    def prune_value(self, value):
        '''Remove value from CURRENT domain'''
        self.curdom[self.value_index(value)] = False

    def unprune_value(self, value):
        '''Restore value to CURRENT domain'''
        self.curdom[self.value_index(value)] = True

    def cur_domain(self):
        '''return list of values in CURRENT domain (if assigned 
           only assigned value is viewed as being in current domain)'''
        vals = []
        if self.is_assigned():
            vals.append(self.get_assigned_value())
        else:
            for i, val in enumerate(self.dom):
                if self.curdom[i]:
                    vals.append(val)
        return vals

    def in_cur_domain(self, value):
        '''check if value is in CURRENT domain (without constructing list)
           if assigned only assigned value is viewed as being in current 
           domain'''
        if not value in self.dom:
            return False
        if self.is_assigned():
            return value == self.get_assigned_value()
        else:
            return self.curdom[self.value_index(value)]

    def cur_domain_size(self):
        '''Return the size of the variables domain (without construcing list)'''
        if self.is_assigned():
            return 1
        else:
            return(sum(1 for v in self.curdom if v))

    def restore_curdom(self):
        '''return all values back into CURRENT domain'''
        for i in range(len(self.curdom)):
            self.curdom[i] = True

    #
    #methods for assigning and unassigning
    #

    def is_assigned(self):
        return self.assignedValue != None
    
    def assign(self, value):
        '''Used by bt_search. When we assign we remove all other values
           values from curdom. We save this information so that we can
           reverse it on unassign'''

        if self.is_assigned() or not self.in_cur_domain(value):
            print("ERROR: trying to assign variable", self, 
                  "that is already assigned or illegal value (not in curdom)")
            return

        self.assignedValue = value

    def unassign(self):
        '''Used by bt_search. Unassign and restore old curdom'''
        if not self.is_assigned():
            print("ERROR: trying to unassign variable", self, " not yet assigned")
            return
        self.assignedValue = None

    def get_assigned_value(self):
        '''return assigned value...returns None if is unassigned'''
        return self.assignedValue

    #
    #internal methods
    #

    def value_index(self, value):
        '''Domain values need not be numbers, so return the index
           in the domain list of a variable value'''
        return self.dom.index(value)

    def __repr__(self):
        return("Var-{}".format(self.name))

    def __str__(self):
        return("Var--{}".format(self.name))

    def print_all(self):
        '''Also print the variable domain and current domain'''
        print("Var--\"{}\": Dom = {}, CurDom = {}".format(self.name, 
                                                             self.dom, 
                                                             self.curdom))


class Constraint:
    """
    Class for defining constraints variable objects specifies an
    ordering over variables.  This ordering is used when calling
    the satisfied function which tests if an assignment to the
    variables in the constraint's scope satisfies the constraint
    """

    def __init__(self, name, scope):
        """
        Create a constraint object, specify the constraint name (a
        string) and its scope (an ORDERED list of variable objects).
        The order of the variables in the scope is critical to the
        functioning of the constraint.

        Constraints are implemented as storing a set of satisfying
        tuples (i.e., each tuple specifies a value for each variable
        in the scope such that this sequence of values satisfies the
        constraints).

        NOTE: This is a very space expensive representation...a proper
        constraint object would allow for representing the constraint
        with a function.

        :param name: Constraint Name
        :type name: str
        :param scope: An ORDERED list of variable objects
        :type scope: iterable[Variable]
        :return: None
        """

        self.scope = list(scope)
        self.name = name
        self.sat_tuples = dict()

        #The next object data item 'sup_tuples' will be used to help
        #support GAC propgation. It allows access to a list of 
        #satisfying tuples that contain a particular variable/value
        #pair.
        self.sup_tuples = dict()

    def add_satisfying_tuples(self, tuples):
        """
        We specify the constraint by adding its complete list of satisfying
        tuples.
        """

        for x in tuples:
            t = tuple(x)  #ensure we have an immutable tuple
            if not t in self.sat_tuples:
                self.sat_tuples[t] = True

            #now put t in as a support for all of the variable values in it
            for i, val in enumerate(t):
                var = self.scope[i]
                if not (var,val) in self.sup_tuples:
                    self.sup_tuples[(var,val)] = []
                self.sup_tuples[(var,val)].append(t)

    def get_scope(self):
        '''get list of variables the constraint is over

        :rtype: list[Variable]'''
        return list(self.scope)

    def check(self, vals) -> bool:
        '''Given list of values, one for each variable in the
           constraints scope, return true if and only if these value
           assignments satisfy the constraint by applying the
           constraints "satisfies" function.  Note the list of values
           are must be ordered in the same order as the list of
           variables in the constraints scope'''
        return tuple(vals) in self.sat_tuples

    def get_n_unasgn(self):
        '''return the number of unassigned variables in the constraint's scope'''
        n = 0
        for v in self.scope:
            if not v.is_assigned():
                n = n + 1
        return n

    def get_unasgn_vars(self): 
        '''return list of unassigned variables in constraint's scope. Note
           more expensive to get the list than to then number'''
        vs = []
        for v in self.scope:
            if not v.is_assigned():
                vs.append(v)
        return vs

    def has_support(self, var, val):
        '''Test if a variable value pair has a supporting tuple (a set
           of assignments satisfying the constraint where each value is
           still in the corresponding variables current domain
        '''
        if (var, val) in self.sup_tuples:
            for t in self.sup_tuples[(var, val)]:
                if self.tuple_is_valid(t):
                    return True
        return False

    def tuple_is_valid(self, t):
        """
        Internal routine. Check if every value in tuple is still in
        corresponding variable domains

        :rtype: boolean
        """
        for i, var in enumerate(self.scope):
            if not var.in_cur_domain(t[i]):
                return False
        return True

    def __str__(self):
        return("{}({})".format(self.name,[var.name for var in self.scope]))


class CSP:
    '''Class for packing up a set of variables into a CSP problem.
       Contains various utility routines for accessing the problem.
       The variables of the CSP can be added later or on initialization.
       The constraints must be added later'''

    def __init__(self, name, vars=[]):
        """
        Create a CSP object. Specify a name (a string) and optionally a set
        of variables

        :param name: Name of CSP
        :type name: str
        :param vars:
        :type vars: iterable[Variable]
        :return:
        """

        self.name = name
        self.vars = []
        self.cons = []
        self.vars_to_cons = dict()
        for v in vars:
            self.add_var(v)

    def add_var(self,v):
        '''Add variable object to CSP while setting up an index
           to obtain the constraints over this variable'''
        if not type(v) is Variable:
            print("Trying to add non variable ", v, " to CSP object")
        elif v in self.vars_to_cons:
            print("Trying to add variable ", v, " to CSP object that already has it")
        else:
            self.vars.append(v)
            self.vars_to_cons[v] = []

    def add_constraint(self,c):
        '''Add constraint to CSP. Note that all variables in the 
           constraints scope must already have been added to the CSP'''
        if not type(c) is Constraint:
            print("Trying to add non constraint ", c, " to CSP object")
        else:
            for v in c.scope:
                if not v in self.vars_to_cons:
                    print("Trying to add constraint ", c, " with unknown variables to CSP object")
                    return
                self.vars_to_cons[v].append(c)
            self.cons.append(c)

    def get_all_cons(self):
        """
        return list of all constraints in the CSP

        :rtype: list[Constraint]
        """
        return self.cons
        
    def get_cons_with_var(self, var):
        """
        return list of constraints that include var in their scope

        :rtype: list[Constraint]
        """
        return list(self.vars_to_cons[var])

    def get_all_vars(self):
        """
        Get all the variables in the CSP

        :return: List of variables in the CSP
        :rtype: list[Variable]
        """

        return list(self.vars)

    def print_all(self):
        print("CSP", self.name)
        print("   Variables = ", self.vars)
        print("   Constraints = ", self.cons)


    def print_soln(self):
        print("CSP", self.name, " Assignments = ")
        for v in self.vars:
            print(v, " = ", v.get_assigned_value(), "    ", end='')
        print("")
