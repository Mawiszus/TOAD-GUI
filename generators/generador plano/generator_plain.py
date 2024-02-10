import os

def generador_dummy():

    directorio_actual = str(os.getcwd)
    ruta_originals = os.path.join(directorio_actual, "..", "levels", "originals")
    ruta_archivo = os.path.join(ruta_originals, "lvl_dummy.txt")

    with open(ruta_archivo, 'w') as archivo:
        cuadricula = ''
        for fila in range(23):
            for columna in range(203):
                if fila <= 20:
                    cuadricula += '-'
                else:
                    cuadricula += 'X'
            cuadricula += '\n'
        archivo.write(cuadricula)

def generador_foso():

    directorio_actual = str(os.getcwd)
    ruta_originals = os.path.join(directorio_actual, "..", "levels", "originals")
    ruta_archivo = os.path.join(ruta_originals, "lvl_foso.txt")

    with open(ruta_archivo, 'w') as archivo:
        cuadricula = ''
        for fila in range(23):
            for columna in range(203):
                if fila <= 20:
                    cuadricula += '-'
                else:
                    cuadricula += 'X' if (columna <= 100 or columna >= 110) else '-' 
            cuadricula += '\n'
        archivo.write(cuadricula)

def generador_pared():

    directorio_actual = str(os.getcwd)
    ruta_originals = os.path.join(directorio_actual, "..", "levels", "originals")
    ruta_archivo = os.path.join(ruta_originals, "lvl_pared.txt")

    columnas_pared = [13, 32, 50, 132]

    with open(ruta_archivo, 'w') as archivo:
        cuadricula = ''
        for fila in range(23):
            for columna in range(203):
                if fila <= 20 and columna not in columnas_pared:
                    cuadricula += '-'
                else:
                    cuadricula += 'X'
            cuadricula += '\n'
        archivo.write(cuadricula)


if __name__=='__main__':
    directorio_actual = str(os.getcwd)
    ruta_originals = os.path.join(directorio_actual, "..", "levels", "originals")
    ruta_archivo = os.path.join(ruta_originals, "lvl_foso.txt")

    generador_dummy()
    generador_foso()
    generador_pared()
        
