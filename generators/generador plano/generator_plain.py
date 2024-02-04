import os

def generator_dummy():

    directorio_actual = str(os.getcwd)
    ruta_originals = os.path.join(directorio_actual, "..", "levels", "originals")
    ruta_archivo = os.path.join(ruta_originals, "lvl_dummy.txt")

    with open(ruta_archivo, 'w') as archivo:
        cuadricula = ''
        for fila in range(23):
            if fila <= 20:
                for _ in range(203):
                    cuadricula += '-'
            else:
                for _ in range(203):
                    cuadricula += 'X'
            cuadricula += '\n'
        archivo.write(cuadricula)

if __name__=='__main__':
    generator_dummy()
        
