import os
from utils.support_functions import comprobar_limite_columnas

directorio_actual = str(os.getcwd)
ruta_originals = os.path.join(directorio_actual, "..", "levels", "originals")

def generador_dummy(num_filas = 20, num_columnas = 200, ancho_suelo = 2):

    ruta_archivo = os.path.join(ruta_originals, "lvl_dummy.txt")

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

def generador_foso(num_filas = 20, num_columnas = 200, ancho_suelo = 2):

    ruta_archivo = os.path.join(ruta_originals, "lvl_foso.txt")

    with open(ruta_archivo, 'w') as archivo:
        cuadricula = ''
        for fila in range(num_filas):
            for columna in range(num_columnas):
                if fila <= num_filas - (ancho_suelo + 1):
                    cuadricula += '-'
                else:
                    cuadricula += 'X' if (columna <= 100 or columna >= 110) else '-' 
            cuadricula += '\n'
        archivo.write(cuadricula)

def generador_pared(num_filas = 20, num_columnas = 200, ancho_suelo = 2, columnas_pared = [10, 15, 40, 201]):

    ruta_archivo = os.path.join(ruta_originals, "lvl_pared.txt")

    if not comprobar_limite_columnas(columnas_pared, num_columnas):
        print('Una de las columnas de la lista sobrepasa el número de columnas del nivel')
    else:
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

    generador_foso(10,130,3)
    generador_pared(10, 140, 4)
