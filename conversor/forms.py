from django import forms

from .conversiones import analizar_texto, convertir_numero


class NumeroForm(forms.Form):
    numero = forms.CharField(
        label="Número",
        error_messages={"required": "Ingrese un número."},
        widget=forms.TextInput(attrs={
            "placeholder": "Por ejemplo: 1010",
            "autocomplete": "off",
            "spellcheck": "false",
            "aria-describedby": "ayuda-numero",
        }),
    )
    base = forms.TypedChoiceField(
        label="Base de origen",
        choices=((2, "Binario · base 2"), (8, "Octal · base 8"),
                 (10, "Decimal · base 10"), (16, "Hexadecimal · base 16")),
        coerce=int,
        initial=10,
        error_messages={
            "required": "Seleccione una base de origen.",
            "invalid_choice": "Seleccione una base válida: 2, 8, 10 o 16.",
        },
    )

    def clean(self):
        datos = super().clean()
        numero = datos.get("numero")
        base = datos.get("base")
        if numero is not None and base is not None:
            try:
                datos["resultado"] = convertir_numero(numero, base)
            except ValueError as error:
                self.add_error("numero", str(error))
        return datos


class TextoForm(forms.Form):
    texto = forms.CharField(
        label="Texto para analizar",
        max_length=20,
        strip=False,
        error_messages={
            "required": "Ingrese un texto.",
            "max_length": "El texto debe tener como máximo 20 caracteres.",
            "null_characters_not_allowed": "El texto no puede contener el carácter nulo.",
        },
        widget=forms.Textarea(attrs={
            "rows": 2,
            "placeholder": "Prueba con Año",
            "aria-describedby": "ayuda-texto",
        }),
    )

    def clean_texto(self):
        texto = self.cleaned_data["texto"]
        try:
            self.resultado = analizar_texto(texto)
        except ValueError as error:
            raise forms.ValidationError(str(error)) from error
        return texto
