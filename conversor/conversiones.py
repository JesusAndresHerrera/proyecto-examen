"""Cálculos del analizador: funciones pequeñas sin acceso a una base de datos."""

import unicodedata


DIGITOS = "0123456789ABCDEF"
BASES_PERMITIDAS = (2, 8, 10, 16)
VALOR_MAXIMO = 65_535


def obtener_decimal(numero, base):
    """Valida los dígitos y suma su valor posicional, de izquierda a derecha."""
    if base not in BASES_PERMITIDAS:
        raise ValueError("Seleccione una base válida: 2, 8, 10 o 16.")

    numero = numero.strip()
    if not numero:
        raise ValueError("Ingrese un número.")
    if numero.startswith("-"):
        raise ValueError("No se permiten valores negativos.")

    permitidos = DIGITOS[:base]
    for digito in numero:
        if digito not in permitidos + permitidos.lower():
            raise ValueError(
                f"El dígito «{digito}» no pertenece a la base {base}. "
                f"Use solamente {permitidos}."
            )

    decimal = 0
    for digito in numero.upper():
        decimal = decimal * base + DIGITOS.index(digito)
        if decimal > VALOR_MAXIMO:
            raise ValueError("El valor debe estar entre 0 y 65 535.")
    return decimal


def representar_en_base(decimal, base):
    """Convierte un entero mediante divisiones sucesivas y sus residuos."""
    if decimal == 0:
        return "0"

    resultado = ""
    while decimal > 0:
        decimal, residuo = divmod(decimal, base)
        resultado = DIGITOS[residuo] + resultado
    return resultado


def convertir_numero(numero, base):
    """Devuelve las cuatro representaciones y su tamaño como dato sin signo."""
    decimal = obtener_decimal(numero, base)
    binario = representar_en_base(decimal, 2)
    bits = 0 if decimal == 0 else len(binario)
    cantidad_bytes = max(1, (bits + 7) // 8)

    return {
        "original": numero.strip(),
        "base": base,
        "decimal": decimal,
        "binario": binario.zfill(cantidad_bytes * 8),
        "octal": representar_en_base(decimal, 8),
        "hexadecimal": representar_en_base(decimal, 16),
        "bits": bits,
        "bytes": cantidad_bytes,
    }


def etiqueta_caracter(caracter):
    """Da un nombre visible a espacios y caracteres que no se pueden imprimir."""
    especiales = {
        " ": "Espacio",
        "\t": "Tabulación",
        "\n": "Salto de línea",
        "\r": "Retorno de carro",
    }
    if caracter in especiales:
        return especiales[caracter]
    if unicodedata.category(caracter).startswith("C"):
        return f"Carácter no visible U+{ord(caracter):04X}"
    if caracter.isspace():
        return f"Espacio U+{ord(caracter):04X}"
    return caracter


def analizar_texto(texto):
    """Analiza hasta veinte puntos de código, sin quitar los espacios."""
    if not texto.strip():
        raise ValueError("Ingrese un texto.")
    if len(texto) > 20:
        raise ValueError("El texto debe tener como máximo 20 caracteres.")

    resultado = []
    for caracter in texto:
        decimal = ord(caracter)
        try:
            datos_utf8 = caracter.encode("utf-8")
        except UnicodeEncodeError as error:
            raise ValueError("El texto contiene un carácter Unicode no válido.") from error
        bytes_utf8 = " ".join(f"{byte:02X}" for byte in datos_utf8)
        resultado.append({
            "caracter": caracter,
            "etiqueta": etiqueta_caracter(caracter),
            "decimal": decimal,
            "punto_codigo": f"U+{decimal:04X}",
            "hexadecimal": f"{decimal:X}",
            "bytes_utf8": bytes_utf8,
            "cantidad_bytes": len(datos_utf8),
        })
    return resultado
