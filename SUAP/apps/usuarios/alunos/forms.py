from apps.usuarios.forms import TipoUsuarioForm
from apps.usuarios.models import Aluno


class AlunoForm(TipoUsuarioForm):
    tipo_valor = "ALUNO"

    class Meta(TipoUsuarioForm.Meta):
        fields = ["first_name", "last_name", "email", "cpf", "is_active"]

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        if commit:
            Aluno.objects.update_or_create(
                pessoa=usuario.pessoa,
                defaults={"usuario": usuario},
            )
        return usuario
