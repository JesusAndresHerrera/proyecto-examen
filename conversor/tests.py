from django.test import SimpleTestCase
from django.urls import reverse

from .conversiones import analizar_texto, convertir_numero, obtener_decimal
from .forms import NumeroForm, TextoForm


class ConversionesNumeroTests(SimpleTestCase):
    def test_cuatro_bases_representan_el_mismo_valor(self):
        for numero, base in (("1010", 2), ("12", 8), ("10", 10), ("A", 16)):
            with self.subTest(numero=numero, base=base):
                resultado = convertir_numero(numero, base)
                self.assertEqual(resultado["decimal"], 10)
                self.assertEqual(resultado["binario"], "00001010")
                self.assertEqual(resultado["octal"], "12")
                self.assertEqual(resultado["hexadecimal"], "A")
                self.assertEqual(resultado["bits"], 4)
                self.assertEqual(resultado["bytes"], 1)

    def test_cero_se_muestra_en_un_byte_con_cero_bits_significativos(self):
        resultado = convertir_numero("0", 10)
        self.assertEqual(resultado["binario"], "00000000")
        self.assertEqual(resultado["bits"], 0)
        self.assertEqual(resultado["bytes"], 1)
        self.assertEqual(resultado["octal"], "0")
        self.assertEqual(resultado["hexadecimal"], "0")

    def test_255_ocupa_exactamente_un_byte(self):
        resultado = convertir_numero("255", 10)
        self.assertEqual(resultado["binario"], "11111111")
        self.assertEqual((resultado["bits"], resultado["bytes"]), (8, 1))

    def test_256_completa_hasta_dos_bytes(self):
        resultado = convertir_numero("256", 10)
        self.assertEqual(resultado["binario"], "0000000100000000")
        self.assertEqual((resultado["bits"], resultado["bytes"]), (9, 2))

    def test_limite_superior_es_valido_en_todas_las_bases(self):
        casos = (("1111111111111111", 2), ("177777", 8),
                 ("65535", 10), ("FFFF", 16))
        for numero, base in casos:
            with self.subTest(base=base):
                resultado = convertir_numero(numero, base)
                self.assertEqual(resultado["decimal"], 65535)
                self.assertEqual(resultado["binario"], "1" * 16)
                self.assertEqual(resultado["hexadecimal"], "FFFF")

    def test_hexadecimal_acepta_minusculas(self):
        self.assertEqual(convertir_numero("ff", 16)["hexadecimal"], "FF")

    def test_ceros_a_la_izquierda_no_aumentan_los_bits(self):
        resultado = convertir_numero("000000001", 2)
        self.assertEqual(resultado["bits"], 1)
        self.assertEqual(resultado["binario"], "00000001")

    def test_digitos_invalidos_indican_la_base(self):
        for numero, base in (("102", 2), ("19", 8), ("1A", 10), ("G", 16)):
            with self.subTest(base=base):
                with self.assertRaisesRegex(ValueError, f"no pertenece a la base {base}"):
                    obtener_decimal(numero, base)

    def test_rechaza_bases_no_permitidas(self):
        for base in (0, 1, 3, 36):
            with self.subTest(base=base):
                with self.assertRaisesRegex(ValueError, "base válida"):
                    obtener_decimal("10", base)

    def test_rechaza_negativos(self):
        with self.assertRaisesRegex(ValueError, "valores negativos"):
            obtener_decimal("-5", 10)

    def test_rechaza_valor_fuera_del_rango_en_todas_las_bases(self):
        for numero, base in (("10000000000000000", 2), ("200000", 8),
                             ("65536", 10), ("10000", 16)):
            with self.subTest(base=base):
                with self.assertRaisesRegex(ValueError, "entre 0 y 65 535"):
                    obtener_decimal(numero, base)

    def test_rechaza_entrada_vacia(self):
        for numero in ("", "   "):
            with self.subTest(numero=numero):
                with self.assertRaisesRegex(ValueError, "Ingrese un número"):
                    obtener_decimal(numero, 10)

    def test_solo_se_permiten_digitos_ascii_sin_prefijos_ni_separadores(self):
        for numero, base in (("１２", 10), ("١٢", 10), ("ﬀ", 16),
                             ("0xFF", 16), ("1_000", 10), ("+5", 10),
                             ("1.5", 10), ("1 0", 2)):
            with self.subTest(numero=numero):
                with self.assertRaisesRegex(ValueError, "no pertenece"):
                    obtener_decimal(numero, base)


class AnalisisTextoTests(SimpleTestCase):
    def test_enie_tiene_dos_bytes_utf8(self):
        fila = analizar_texto("ñ")[0]
        self.assertEqual(fila["caracter"], "ñ")
        self.assertEqual(fila["decimal"], 241)
        self.assertEqual(fila["punto_codigo"], "U+00F1")
        self.assertEqual(fila["hexadecimal"], "F1")
        self.assertEqual(fila["bytes_utf8"], "C3 B1")
        self.assertEqual(fila["cantidad_bytes"], 2)

    def test_texto_ascii_y_enie_se_analiza_en_orden(self):
        filas = analizar_texto("Año")
        self.assertEqual([fila["decimal"] for fila in filas], [65, 241, 111])
        self.assertEqual([fila["bytes_utf8"] for fila in filas], ["41", "C3 B1", "6F"])

    def test_emoji_tiene_punto_de_codigo_y_cuatro_bytes(self):
        fila = analizar_texto("😀")[0]
        self.assertEqual(fila["punto_codigo"], "U+1F600")
        self.assertEqual(fila["bytes_utf8"], "F0 9F 98 80")
        self.assertEqual(fila["cantidad_bytes"], 4)

    def test_espacios_y_saltos_de_linea_se_conservan(self):
        filas = analizar_texto(" A\n\t")
        self.assertEqual(len(filas), 4)
        self.assertEqual([fila["etiqueta"] for fila in filas],
                         ["Espacio", "A", "Salto de línea", "Tabulación"])
        self.assertEqual([fila["bytes_utf8"] for fila in filas], ["20", "41", "0A", "09"])

    def test_limite_veinte_cuenta_puntos_de_codigo_y_no_bytes(self):
        self.assertEqual(len(analizar_texto("ñ" * 20)), 20)
        self.assertEqual(len(analizar_texto("😀" * 20)), 20)
        with self.assertRaisesRegex(ValueError, "máximo 20"):
            analizar_texto("a" * 21)

    def test_texto_vacio_es_invalido(self):
        for texto in ("", "   ", "\n\t"):
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, "Ingrese un texto"):
                    analizar_texto(texto)


class FormulariosTests(SimpleTestCase):
    def test_formulario_numero_acepta_espacios_exteriores_y_preserva_numero(self):
        formulario = NumeroForm({"numero": "  000a  ", "base": "16"})
        self.assertTrue(formulario.is_valid(), formulario.errors)
        self.assertEqual(formulario.cleaned_data["resultado"]["decimal"], 10)
        self.assertEqual(formulario.cleaned_data["numero"], "000a")

    def test_formulario_distingue_error_de_base_del_numero(self):
        formulario = NumeroForm({"numero": "10", "base": "3"})
        self.assertFalse(formulario.is_valid())
        self.assertIn("base", formulario.errors)
        self.assertNotIn("numero", formulario.errors)

    def test_formulario_texto_conserva_espacios_con_caracteres(self):
        formulario = TextoForm({"texto": " A ñ "})
        self.assertTrue(formulario.is_valid(), formulario.errors)
        self.assertEqual(formulario.cleaned_data["texto"], " A ñ ")
        self.assertEqual(len(formulario.resultado), 5)
        self.assertEqual(formulario.resultado[0]["bytes_utf8"], "20")

    def test_formulario_texto_rechaza_solo_espacios(self):
        formulario = TextoForm({"texto": "   "})
        self.assertFalse(formulario.is_valid())
        self.assertIn("Ingrese un texto", formulario.errors["texto"][0])

    def test_formulario_texto_rechaza_mas_de_veinte_caracteres(self):
        formulario = TextoForm({"texto": "ñ" * 21})
        self.assertFalse(formulario.is_valid())
        self.assertIn("máximo 20", formulario.errors["texto"][0])


class PaginaTests(SimpleTestCase):
    def setUp(self):
        self.url = reverse("conversor:analizar")

    def test_get_muestra_ambos_formularios_sin_errores(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Analizador de representación de datos")
        self.assertFalse(respuesta.context["form_numero"].is_bound)
        self.assertFalse(respuesta.context["form_texto"].is_bound)
        self.assertIsNone(respuesta.context["resultado_numero"])

    def test_post_numero_no_valida_el_formulario_texto(self):
        respuesta = self.client.post(self.url, {"accion": "numero", "numero": "1010", "base": "2"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "00001010")
        self.assertEqual(respuesta.context["resultado_numero"]["decimal"], 10)
        self.assertFalse(respuesta.context["form_texto"].is_bound)

    def test_post_texto_no_valida_el_formulario_numero(self):
        respuesta = self.client.post(self.url, {"accion": "texto", "texto": "Año"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "C3 B1")
        self.assertEqual(len(respuesta.context["resultado_texto"]), 3)
        self.assertFalse(respuesta.context["form_numero"].is_bound)

    def test_error_numero_preserva_la_entrada_y_no_produce_resultado(self):
        respuesta = self.client.post(self.url, {"accion": "numero", "numero": "102", "base": "2"})
        self.assertIsNone(respuesta.context["resultado_numero"])
        self.assertEqual(respuesta.context["form_numero"]["numero"].value(), "102")
        self.assertContains(respuesta, "no pertenece a la base 2")

    def test_entradas_vacias_muestran_errores_especificos(self):
        for datos, campo, mensaje in (
            ({"accion": "numero", "numero": "", "base": "10"}, "form_numero", "Ingrese un número"),
            ({"accion": "texto", "texto": ""}, "form_texto", "Ingrese un texto"),
        ):
            with self.subTest(datos=datos):
                respuesta = self.client.post(self.url, datos)
                self.assertTrue(respuesta.context[campo].errors)
                self.assertContains(respuesta, mensaje)

    def test_accion_desconocida_muestra_mensaje_claro(self):
        respuesta = self.client.post(self.url, {"accion": "otra"})
        self.assertContains(respuesta, "Seleccione Analizar número o Analizar texto")
        self.assertIsNone(respuesta.context["resultado_numero"])
        self.assertIsNone(respuesta.context["resultado_texto"])

    def test_caracteres_html_se_escapan(self):
        respuesta = self.client.post(self.url, {"accion": "texto", "texto": "<>&"})
        self.assertContains(respuesta, "&lt;")
        self.assertContains(respuesta, "&gt;")

    def test_formularios_protegen_post_con_csrf(self):
        from django.test import Client

        cliente = Client(enforce_csrf_checks=True)
        respuesta = cliente.post(self.url, {"accion": "numero", "numero": "10", "base": "10"})
        self.assertEqual(respuesta.status_code, 403)
