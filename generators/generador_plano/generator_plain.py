import os


current_directory = str(os.getcwd)
originals_path = os.path.join(current_directory, "..", "levels", "originals")

def dummy_generator(num_rows = 20, num_columns = 200, floor_width = 2):
    
    file_path = os.path.join(originals_path, "lvl_dummy.txt")

    #lvl generation
    with open(file_path, 'w') as file:
        grid = ''
        for row in range(num_rows):
            for _ in range(num_columns):
                if row <= num_rows - (floor_width + 1):
                    grid += '-'
                else:
                    grid += 'X'
            grid += '\n'
        file.write(grid)

    return file_path

def pit_lvl_generator(num_rows = 20, num_columns = 200, floor_width = 2, pit_position = 30, pit_length = 13):

    file_path = os.path.join(originals_path, "lvl_foso.txt")

    #lvl generation
    with open(file_path, 'w') as file:
        grid = ''
        for fila in range(num_rows):
            for columna in range(num_columns):
                if fila <= num_rows - (floor_width + 1):
                    grid += '-'
                else:
                    grid += 'X' if (columna < pit_position or columna > pit_position + (pit_length - 1)) else '-' 
            grid += '\n'
        file.write(grid)
    
    return file_path

def wall_lvl_generator(num_rows = 20, num_columns = 200, floor_width = 2, wall_columns = [10, 15, 40, 180]):

    file_path = os.path.join(originals_path, "lvl_pared.txt")

    #Generación del nivel
    with open(file_path, 'w') as file:
        cuadricula = ''
        for fila in range(num_rows):
            for columna in range(num_columns):
                if fila <= (num_rows - (floor_width + 1)) and columna not in wall_columns:
                    cuadricula += '-'
                else:
                    cuadricula += 'X'
            cuadricula += '\n'
        file.write(cuadricula)
            
    return file_path

if __name__=='__main__':

    pit_lvl_generator(10,130,3, 110, 20)
    wall_lvl_generator(10, 200, 4)
