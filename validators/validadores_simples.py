import os

def validar_foso_pasable(lvl):

    matriz_transpuesta = transpose_file(lvl)
    lista_fosos = []
    es_pasable = False

    #Comprobar longitud de los fosos del mapa
    for i, fila_transpuesta in enumerate(matriz_transpuesta):
        if 'X' in matriz_transpuesta[i - 1] and set(fila_transpuesta) == {'-'}:
            contador_filas = 0
        if set(fila_transpuesta) == {'-'}:
            contador_filas += 1
        if set(fila_transpuesta) == {'-'} and 'X' in matriz_transpuesta[i + 1]:
            lista_fosos.append(contador_filas)

    #Comprobar si alguna de las longitudes es mayor que la distancia de salto de mario
    if all(n <= 8 for n in lista_fosos):
        es_pasable = True

    return es_pasable

def validar_pared_pasable(lvl):

    matriz_transpuesta = transpose_file(lvl)
    es_pasable = True

    for i in range(len(matriz_transpuesta) - 1):

        #longitud de la pared en la columna actual
        fila_invertida = matriz_transpuesta[i][::-1]
        encontrar_hueco = fila_invertida.find('-')
        longitud_pared = fila_invertida[:encontrar_hueco].count('X')

        #longitud de la pared en la columna siguiente
        fila_invertida_siguiente = ''.join(reversed(matriz_transpuesta[i + 1]))
        encontrar_hueco_siguiente = fila_invertida_siguiente.find('-')
        longitud_pared_siguiente = fila_invertida_siguiente[:encontrar_hueco_siguiente].count('X')

        #Comprueba si la diferencia de longitudes de las paredes es mayor que el salto más alto de mario
        if (longitud_pared - longitud_pared_siguiente) > 4:
            es_pasable = False
            break

    return es_pasable

def transpose_file(input_file):
        
    with open(input_file, 'r') as file:
        filas = [line.strip() for line in file.readlines()]

   
    num_filas = len(filas)
    num_columnas = len(filas[0])
    matriz_transpuesta = [''.join(filas[j][i] for j in range(num_filas)) for i in range(num_columnas)]
   
    return matriz_transpuesta

if __name__=='__main__':

    directorio_actual = str(os.getcwd)
    ruta_originals = os.path.join(directorio_actual, "..", "levels", "originals")
    ruta_archivo = os.path.join(ruta_originals, "lvl_pared.txt")

    print(validar_pared_pasable(ruta_archivo))


