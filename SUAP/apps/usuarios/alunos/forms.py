from apps.usuarios.forms import TipoUsuarioForm


class AlunoForm(TipoUsuarioForm):
    tipo_valor = "ALUNO"

    class Meta(TipoUsuarioForm.Meta):
        fields = ["first_name", "last_name", "email", "cpf", "is_active"]

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if not usuario.username:
            usuario.username = usuario.cpf
        if commit:
            usuario.save()
        return usuario
