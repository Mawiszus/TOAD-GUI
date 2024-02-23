import os

directorio_actual = str(os.getcwd)
ruta_originals = os.path.join(directorio_actual, "..", "levels", "originals")

def comprobar_limite_columnas(lista, limite):
    """ 
     Comprueba que ningun número de la lista sobrepasa el limite que se le pasa como parametro
    """
    for numero in lista:
        if numero > limite:
            return False  
    return True  

def generador_dummy(num_filas = 20, num_columnas = 200, ancho_suelo = 2):
    
    ruta_archivo = os.path.join(ruta_originals, "lvl_dummy.txt")

    #Generación del nivel
    with open(ruta_archivo, 'w') as archivo:
        cuadricula = ''
        for fila in range(num_filas):
            for _ in range(num_columnas):
                if fila <= num_filas - (ancho_suelo + 1):
                    cuadricula += '-'
                else:
                    cuadricula += 'X'
            cuadricula += '\n'
        archivo.write(cuadricula)

def generador_foso(num_filas = 20, num_columnas = 200, ancho_suelo = 2, posicion_foso = 30, largo_foso = 13):

    ruta_archivo = os.path.join(ruta_originals, "lvl_foso.txt")

    #Comprueba que los parametros son validos
    if posicion_foso >= num_columnas:
        print('La posición indicada para el foso esta fuera del rango del nivel')
    elif posicion_foso + largo_foso > num_columnas:
        print('Esta configuración de largo del foso y posición se salen del rango del nivel')  
    else:
    #Generación del nivel
        with open(ruta_archivo, 'w') as archivo:
            cuadricula = ''
            for fila in range(num_filas):
                for columna in range(num_columnas):
                    if fila <= num_filas - (ancho_suelo + 1):
                        cuadricula += '-'
                    else:
                        cuadricula += 'X' if (columna < posicion_foso or columna > posicion_foso + (largo_foso - 1)) else '-' 
                cuadricula += '\n'
            archivo.write(cuadricula)

def generador_pared(num_filas = 20, num_columnas = 200, ancho_suelo = 2, columnas_pared = [10, 15, 40, 180]):

    ruta_archivo = os.path.join(ruta_originals, "lvl_pared.txt")

    #Comprueba que los parametros son validos
    if not comprobar_limite_columnas(columnas_pared, num_columnas):
        print('Una de las columnas de la lista sobrepasa el número de columnas del nivel')
    else:
    #Generación del nivel
        with open(ruta_archivo, 'w') as archivo:
            cuadricula = ''
            for fila in range(num_filas):
                for columna in range(num_columnas):
                    if fila <= (num_filas - (ancho_suelo + 1)) and columna not in columnas_pared:
                        cuadricula += '-'
                    else:
                        cuadricula += 'X'
                cuadricula += '\n'
            archivo.write(cuadricula)

if __name__=='__main__':

    generador_foso(10,130,3, 110, 20)
    generador_pared(10, 200, 4)
