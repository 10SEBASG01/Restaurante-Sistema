
def __init__(self, *args, **kwargs):

    super().__init__(*args, **kwargs)

    mesas_disponibles = Mesa.objects.filter( #type: ignore
        estado='libre'
    ).order_by('numero')

    opciones = [
        ('', 'Seleccione una mesa')
    ]

    for mesa in mesas_disponibles:

        opciones.append(
            (
                f"Mesa {mesa.numero}",
                f"Mesa {mesa.numero} - {mesa.capacidad} personas"
            )
        )

    # Si estamos editando una reserva
    if self.instance and self.instance.pk:

        mesa_actual = self.instance.mesa

        existe = any(
            opcion[0] == mesa_actual
            for opcion in opciones
        )

        if not existe:

            opciones.append(
                (
                    mesa_actual,
                    f"{mesa_actual} (Actual)"
                )
            )

    self.fields['mesa'].choices = opciones