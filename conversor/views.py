from django.shortcuts import render

from .forms import NumeroForm, TextoForm


def analizar(request):
    """Cada botón valida únicamente el formulario que envió el usuario."""
    form_numero = NumeroForm()
    form_texto = TextoForm()
    resultado_numero = None
    resultado_texto = None
    error_accion = None

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "numero":
            form_numero = NumeroForm(request.POST)
            if form_numero.is_valid():
                resultado_numero = form_numero.cleaned_data["resultado"]
        elif accion == "texto":
            form_texto = TextoForm(request.POST)
            if form_texto.is_valid():
                resultado_texto = form_texto.resultado
        else:
            error_accion = "Seleccione Analizar número o Analizar texto para continuar."

    return render(request, "conversor/index.html", {
        "form_numero": form_numero,
        "form_texto": form_texto,
        "resultado_numero": resultado_numero,
        "resultado_texto": resultado_texto,
        "error_accion": error_accion,
    })
