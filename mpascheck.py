# mpascheck.py
# -*- coding: utf-8 -*-
'''
Proyecto 3 : Chequeo del Programa
=================================
En este proyecto es necesario realizar comprobaciones sem�nticas en su programa. 
Hay algunos aspectos diferentes para hacer esto.

En primer lugar, tendr� que definir una tabla de s�mbolos que haga un seguimiento
de declaraciones de identificadores previamente declarados.  Se consultar� la 
tabla de s�mbolos siempre que el compilador necesite buscar informaci�n sobre 
variables y declaraci�n de constantes.

A continuaci�n, tendr� que definir los objetos que representen los diferentes 
tipos de datos incorporados y registrar informaci�n acerca de sus capacidades.
Revise el archivo mpastype.py.

Por �ltimo, tendr� que escribir c�digo que camine por el AST y haga cumplir un
conjunto de reglas sem�nticas.  Aqu� est� una lista completa de todo los que
deber� comprobar:

1.  Nombres y s�mbolos:

    Todos los identificadores deben ser definidos antes de ser usados.  Esto incluye variables, 
    constantes y nombres de tipo.  Por ejemplo, esta clase de c�digo genera un error:
    
       a = 3;              // Error. 'a' no est� definido.
       var a int;

    Note: los nombres de tipo como "int", "float" y "string" son nombres incorporados que
    deben ser definidos al comienzo de un programa (funci�n).
    
2.  Tipos de constantes

    A todos los s�mbolos constantes se le debe asignar un tipo como "int", "float" o "string".
    Por ejemplo:

       const a = 42;         // Tipo "int"
       const b = 4.2;        // Tipo "float"
       const c = "forty";    // Tipo "string"

    Para hacer esta asignaci�n, revise el tipo de Python del valor constante y adjunte el
    nombre de tipo apropiado.

3.  Chequeo de tipo operaci�n binaria.

    Operaciones binarias solamente operan sobre operandos del mismo tipo y produce un
    resultado del mismo tipo.  De lo contrario, se tiene un error de tipo.  Por ejemplo:

    var a int = 2;
    var b float = 3.14;

    var c int = a + 3;    // OK
    var d int = a + b;    // Error.  int + float
    var e int = b + 4.5;  // Error.  int = float

4.  Chequeo de tipo operador unario.

    Operadores unarios retornan un resultado que es del mismo tipo del operando.

5.  Operadores soportados

    Estos son los operadores soportados por cada tipo:

    int:      binario { +, -, *, /}, unario { +, -}
    float:    binario { +, -, *, /}, unario { +, -}
    string:   binario { + }, unario { }

    Los intentos de usar operadores no soportados deber�a dar lugar a un error.
    Por ejemplo:

    var string a = "Hello" + "World";     // OK
    var string b = "Hello" * "World";     // Error (op no soportado *)

6.  Asignaci�n.

    Los lados izquierdo y derecho de una operaci�n de asignaci�n deben ser 
    declarados del mismo tipo.

    Los valores s�lo se pueden asignar a las declaraciones de variables, no
    a constantes.

Para recorrer el AST, use la clase NodeVisitor definida en mpasast.py.
Un caparaz�n de c�digo se proporciona a continuaci�n.
'''

import sys, re, string, types
from errors import error
from mpasast import *
import mpastype
import mpaslex

class SymbolTable(object):
  '''
  Clase que representa una tabla de s�mbolos.  Debe proporcionar funcionabilidad
  para agregar y buscar nodos asociados con identificadores.
  '''
  def __init__(self, parent=None):
    '''
    Crea una tabla se s�mbol vacia con la tabla de s�mbol
    padre.
    '''

    self.entries = {}
    self.parent = parent
    if self.parent != None:
      self.parent.children.append(self)
    self.children = []
  def lookup(self, a):
    return self.entries.get(a)

  def add(self, name, value):
    '''
    Agrega un s�mbol con el valor dado a la tabla de s�mbol.
    El valor es usualmente un nodo del AST que representa la
    declaraci�n o definici�n de una funci�n/variable (p.e.,
    Declaration o FunctionDefn).
    '''
    
    if self.entries.has_key(name):
      if not self.entries[name].extern:
        raise Symtab.SymbolDefinedError()
      elif self.entries[name].type.get_string() != \
        value.type.get_string():
        raise Symtab.SymbolConflictError()
    self.entries[name] = value

  def get(self, name):
    '''
    Recupera el s�mbol con el nombre dado desde la tabla de
    s�mbolos, recursivamente hacia arriba a trav�s del padre
    si no se encuentra en la actual.
    '''

    if self.entries.has_key(name):
      return self.entries[name]
    else:
      if self.parent != None:
        return self.parent.get(name)
      else:
        return None




class CheckProgramVisitor(NodeVisitor):
  '''
  Clase de Revisi�n de programa.  Esta clase usa el patr�n cisitor como est�
  descrito en mpasast.py.  Es necesario definir m�todos de la forma visit_NodeName()
  para cada tipo de nodo del AST que se desee procesar.

  Nota: Usted tendr� que ajustar los nombres de los nodos del AST si ha elegido
  nombres diferentes.
  '''
  def __init__(self):
    # Inicializa la tabla de simbolos
    self.symtab = SymbolTable()

    # Agrega nombre de tipos incorporados ((int, float, string) a la tabla de simbolos
    self.symtab.add("int",mpastype.int_type)
    self.symtab.add("float",mpastype.float_type)
    self.symtab.add("string",mpastype.string_type)
    self.symtab.add("bool",mpastype.boolean_type)

  def visit_Program(self,node):
    # 1. Visita todas las declaraciones (statements)
    # 2. Registra la tabla de simbolos asociada
    for i in node.function:
      self.visit(i)

  def visit_IfStatement(self, node):
    self.visit(node.cond)
    if not node.cond.type == mpastype.boolean_type:
      error(node.lineno, "Tipo incorrecto para condici�n if")
    else:
      self.visit(node.then_b)
      if node.else_b:
        self.visit(node.else_b)

  def visit_WhileStatement(self, node):
    self.visit(node.cond)
    if not node.cond.type == mpastype.boolean_type:
      error(node.lineno, "Tipo incorrecto para condici�n while")
    else:
      self.visit(node.body)

  def visit_UnaryOp(self, node):
    # 1. Aseg�rese que la operaci�n es compatible con el tipo
    # 2. Ajuste el tipo resultante al mismo del operando
    self.visit(node.right)
    if not mpaslex.operators[node.op] in node.right.type.un_ops:
      error(node.lineno, "Operaci�n no soportada con este tipo")
    node.type = node.right.type

  def visit_BinaryOp(self, node):
    # 1. Aseg�rese que los operandos left y right tienen el mismo tipo
    # 2. Aseg�rese que la operaci�n est� soportada
    # 3. Asigne el tipo resultante
    self.visit(node.left)
    self.visit(node.right)
    if node.left.type != node.right.type:
      error(node.lineno, "No coinciden los tipos de los operandos en la operacion con %s" % node.op)
    node.type = node.left.type

  def visit_AssignmentStatement(self,node):
    # 1. Aseg�rese que la localizaci�n de la asignaci�n est� definida
    sym = self.symtab.lookup(node.location)
    assert sym, "Asignado a un sym desconocido"
    # 2. Revise que la asignaci�n es permitida, pe. sym no es una constante
    # 3. Revise que los tipos coincidan.
    self.visit(node.value)
    assert sym.type == node.value.type, "Tipos no coinciden en asignaci�n"

  def visit_ConstDeclaration(self,node):
    # 1. Revise que el nombre de la constante no se ha definido
    if self.symtab.lookup(node.id):
      error(node.lineno, "S�mbol %s ya definido" % node.id)
    # 2. Agrege una entrada a la tabla de s�mbolos
    else:
      self.symtab.add(node.id, node)
    self.visit(node.value)
    node.type = node.value.type

  def visit_VarDeclaration(self,node):
    # 1. Revise que el nombre de la variable no se ha definido
    if self.symtab.lookup(node.id):
      error(node.lineno, "S�mbol %s ya definido" % node.id)
    # 2. Agrege la entrada a la tabla de s�mbolos
    else:
      self.symtab.add(node.id, node)
    # 2. Revise que el tipo de la expresi�n (si lo hay) es el mismo
    if node.value:
      self.visit(node.value)
      assert(node.typename == node.value.type.name)
    # 4. Si no hay expresi�n, establecer un valor inicial para el valor
    else:
      node.value = None
    node.type = self.symtab.lookup(node.typename)
    assert(node.type)

  def visit_Location(self,node):
    # 1. Revisar que la localizaci�n es una variable v�lida o un valor constante
    # 2. Asigne el tipo de la localizaci�n al nodo
    if node.pos:
    	self.visit(node.pos)
    	if node.pos.type != self.symtab.lookup("int") : 
    		error(node.lineno, "Acceso invalido al vector")
    if self.symtab.lookup(node.id):
    	node.type = self.symtab.lookup(node.id)
    else:
    	error(node.lineno, "El id %s no ha sido definido" % node.id)

  def visit_Literal(self,node):
    # Adjunte un tipo apropiado a la constante
    if isinstance(node.value, types.BooleanType):
      node.type = self.symtab.lookup("bool")
    elif isinstance(node.value, types.IntType):
      node.type = self.symtab.lookup("int")
    elif isinstance(node.value, types.FloatType):
      node.type = self.symtab.lookup("float")
    elif isinstance(node.value, types.StringTypes):
      node.type = self.symtab.lookup("string")

  def visit_Funcdecl(self, node):
    if self.symtab.lookup(node.id):
      error(node.lineno, "S�mbol %s ya definido" % node.id)
    self.visit(node.parameters)
    self.visit(node.locals)
    self.visit(node.statements)

  def visit_Parameters(self, node):
    for p in node.parameters:
      self.visit(p)
#falta
  def visit_Parameters_Declaration(self, node):
    node.type = self.symtab.lookup(node.typename)

  def visit_Group(self, node):
    self.visit(node.expression)
    node.type = node.expression.type

  def visit_RelationalOp(self, node):
    self.visit(node.left)
    self.visit(node.right)
    if not node.left.type == node.right.type:
      error(node.lineno, "Operandos de relaci�n no son del mismo tipo")
    elif not mpaslex.operators[node.op] in node.left.type.bin_ops:
      error(node.lineno, "Operaci�n no soportada con este tipo")
    node.type = self.symtab.lookup('bool')

  def visit_FunCall(self, node):
    pass
  def visit_ExprList(self, node):
    pass

  def visit_Empty(self, node):
    pass

  def push_symtab(self, node):
    '''
    Inserta una tabla de s�mbolos dentro de la pila de tablas de
    s�mbolos del visitor y adjunta esta tabla de s�mbolos al nodo
    dado.  Se utiliza siempre que un �mbito l�xico es encontrado,
    por lo que el nodo es un objeto CompoundStatement.
    '''

    self.curr_symtab = Symtab(self.curr_symtab)
    node.symtab = self.curr_symtab

  def pop_symtab(self):
    '''
    Extrae una tabla de s�mbolos de la pila de tablas de s�mbol
    del visitor.  Se utiliza cuando se sale de un �mbito l�xico.
    '''

    self.curr_symtab = self.curr_symtab.parent

  def generic_visit(self,node):
    if getattr(node,"_fields") : 
      for field in getattr(node,"_fields"):
        value = getattr(node,field,None)
        if isinstance(value, list):
          for item in value:
            if isinstance(item,AST):
              self.visit(item)
        elif isinstance(value, AST):
          self.visit(value)
    else :
      pass



# ----------------------------------------------------------------------
#                       NO MODIFICAR NADA DE LO DE ABAJO
# ----------------------------------------------------------------------

def check_program(node):
  '''
  Comprueba el programa suministrado (en forma de un AST)
  '''
  checker = CheckProgramVisitor()
  checker.visit(node)

def main():
  import mpasparse
  import sys
  from errors import subscribe_errors
  lexer = mpaslex.make_lexer()
  parser = mpasparse.make_parser()
  with subscribe_errors(lambda msg: sys.stdout.write(msg+"\n")):
    program = parser.parse(open(sys.argv[1]).read())
    # Revisa el programa
    check_program(program)

if __name__ == '__main__':
  main()
