import re
import subprocess
from collections import Counter
import csv
import datetime


def decode_instruction(instruction_hex):
    """Decodificar la instrucción hexadecimal usando `xed`."""
    try:
        # Ejecutar el comando xed para decodificar la instrucción
        result = subprocess.run(['xed', '-decode', instruction_hex], capture_output=True, text=True)
        decoded_instruction = result.stdout.strip()
        return decoded_instruction
    except Exception as e:
        return f"Error al decodificar: {e}"

def extract_instruction_coverage(file_path):
    with open(file_path, 'r') as file:
        data = file.readlines()

    instruction_counter = Counter()

    # Buscar las instrucciones ejecutadas en el archivo de salida
    instruction_pattern = re.compile(r"^Executed instruction: ([0-9A-Fa-f ]+)")
    
    for line in data:
        match = instruction_pattern.match(line)
        if match:
            instruction = match.group(1).strip()
            instruction_counter[instruction] += 1

    return instruction_counter

def extract_branch_coverage(file_path):
    with open(file_path, 'r') as file:
        data = file.readlines()

    branch_counter = Counter()

    # Buscar las ramas ejecutadas en el archivo de salida
    branch_pattern = re.compile(r"^Branch executed: (\S+)")
    
    for line in data:
        match = branch_pattern.match(line)
        if match:
            branch_address = match.group(1)
            branch_counter[branch_address] += 1

    return branch_counter

def generate_coverage_report(instruction_coverage, branch_coverage):
    report_file = "coverage_report.csv"
    
    # Escribir encabezados si el archivo no existe
    file_exists = False
    try:
        with open(report_file, 'r') as f:
            file_exists = True
    except FileNotFoundError:
        pass

    # Datos de instrucciones
    instruction_data = [{"timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                          "instruction": inst,
                          "execution_count": count,
                          "decoded_instruction": decode_instruction(inst)}
                         for inst, count in instruction_coverage.items()]

    # Datos de ramas
    branch_data = [{"timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "branch": branch, "execution_count": count}
                   for branch, count in branch_coverage.items()]

    # Escribir el reporte en el CSV
    with open(report_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "instruction", "execution_count", "decoded_instruction"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(instruction_data)
        writer.writerows(branch_data)
    
    print("Reporte de cobertura generado con éxito.")

# Ejecutar el análisis de cobertura de instrucciones y ramas
instruction_coverage = extract_instruction_coverage('coverage_output.txt')
branch_coverage = extract_branch_coverage('coverage_output.txt')

# Mostrar las instrucciones más ejecutadas
print("Instrucciones más ejecutadas:")
for instruction, count in instruction_coverage.most_common(10):
    decoded = decode_instruction(instruction)
    print(f"Instrucción: {instruction}, Ejecutada: {count} veces, Decodificada: {decoded}")

# Mostrar las ramas más ejecutadas
print("\nRamas más ejecutadas:")
for branch, count in branch_coverage.most_common(10):
    print(f"Rama: {branch}, Ejecutada: {count} veces")

# Generar el reporte de cobertura
generate_coverage_report(instruction_coverage, branch_coverage)
