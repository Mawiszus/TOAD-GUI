def comprobar_limite_columnas(lista, limite):
    """ 
     Comprueba que ningun número de la lista sobrepasa el limite que se le pasa como parametro
    """
    for numero in lista:
        if numero > limite:
            return False  
    return True  