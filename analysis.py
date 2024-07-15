import ast
import pathlib
import nnf
import AST_modify as AST

def extract(f):
    with open(f, "r") as source:
        tree = ast.parse(source.read())

    t = AST.MyTransformer()  # Transform tree (write logic to tree)
    t.find_parents(tree, None) # Gets parents for every node in the tree
    t.visit(tree)

    s = AST.MyVisitor()  # Get logic from tree (visit tree)
    s.visit(tree)
    
    result = s.list
    return f, result

# Each of these methods takes in a formula and returns an analysis

def check_dead_code(f):
    """Checks if it is satisfiable (at least one model). If not, the code will never be run."""
    return f.satisfiable()


def check_vacuously_holds(f):
    """Checks if every assignment to the variables is true."""
    # Equivalent to if the negation is not satisfiable.
    return not(f.negate().satisfiable())


def compute_irrelevant_vars(f):
    """Computes which variables don't play a role."""
    # This holds for a variable v when (f&v) is equivalent to (f&~v), once v is projected away
    # f.forget_aux() returns a theory that forgets all of the auxillary variables
#    v = nnf.Var('V')
#    if f.equivalent(v) == True:
#        f = f.forget(v)
    return f.forget_aux()


def compute_restriction(f):
    """Computes how restricted this conditional is."""
    # Should be 1 - (<solutions to f> / 2^<variables in f>)
    # model_count() → int : Return the number of models the sentence has.
    # vars() -> FrozenSet[Hashable]: The names of all variables that appear in the sentence.
    numofvars = len(f.vars())
    sol = f.model_count() / (2 ** numofvars)
    restriction = 1 - sol
    return restriction


def compute_entropy(f):
    """Computes the complexity of the formula."""
    # Should be 1 - |2*((<solutions to f> / 2^<variables in f>) - 0.5)|
    #   solution_likelihood = (<solutions to f> / 2^<variables in f>)
    #   shifted = solution_likelihood - 0.5 # Between -0.5 and +0.5
    #   scaled = shifted * 2 # Between -1 and +1
    #   absolute = |scaled| # Between 0 and +1
    #   entropy = 1-absolute # This isn't actually the entropy, but gets close enough to what we want.
    numofvars = len(f.vars())
    sol = f.model_count() / (2 ** numofvars)
    shifted = sol - 0.5
    scaled = shifted * 2
    absolute = abs(scaled)
    entropy = 1 - absolute
    return entropy


if __name__ == "__main__":
    p = pathlib.Path("clones").glob('**/*') # Identify all python files in cloned repos
    files = [x for x in p if x.suffix == '.py']
    dirs = 0
    for x in pathlib.Path('clones').iterdir(): # Get num of directories
        dirs += 1
    output = open("output analysis.txt","w+") # Write to text file
    output.write("******\n")
    output.write("ANALYSIS IS IN THE FORM OF: \n\nFile_name.py\n[(Logic, Line num., Restriction value, Complexity value)]\n\n")
    output.write("NOTES:\n")
    output.write("Empty list [] means no conditionals present in file\n")
    output.write("In some cases, error parsing file results from uncaught complex conditional edge cases (to be fixed in future work)\n")
    output.write("******\n\n")
    output.write("Total {0} Python files in {1} repositories\n\n".format(len(files),dirs))

    for i in files:
        try:
            extracted = extract(i)
            array = extracted[1]
            nnfarray = extracted
            values = []
            result = []

            for tuples in array:
                f = tuples[0]
                try:
                    check_dead_code(f)
                    # print(check_dead_code(f))
                except False:
                    print("Dead code.")
                    pass
                else:
                    try:
                        check_vacuously_holds(f)
                    except False:
                        print("The formula holds vacuously.")
                        pass
                    else:
                        f = compute_irrelevant_vars(f)
                        result.append((tuples[0],tuples[1], compute_restriction(f), compute_entropy(f)))
            
            output.write(str(i)+'\n')
            output.write(str(result)+'\n\n')

        except Exception as e:
            output.write('Error parsing file: {0} ({1})\n\n'.format(i,e))